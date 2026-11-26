import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
)


class RandomForestDetector:
    """Random Forest classifier for TESS transit detection."""

    def __init__(self, params_dict):
        self.csv_path = params_dict["csv_path"]
        self.n_bins = params_dict.get("n_bins", 1000)
        self.use_scaler = params_dict.get("use_scaler", False)
        self.samples_per_class = params_dict.get("samples_per_class", 350)
        self.test_size = params_dict.get("test_size", 0.2)
        self.random_state = params_dict.get("random_state", 42)

        # RF hyperparameters
        self.n_estimators = params_dict.get("n_estimators", 500)
        self.max_depth = params_dict.get("max_depth", None)
        self.min_samples_leaf = params_dict.get("min_samples_leaf", 1)
        self.max_features = params_dict.get("max_features", "sqrt")

        # Output options
        self.output_dir = params_dict.get("output_dir", ".")
        self.save_plots = params_dict.get("save_plots", True)
        self.save_model = params_dict.get("save_model", False)

    def _create_balanced_dataset(self, X, y):
        rng = np.random.default_rng(self.random_state)
        X0, X1 = X[y == 0], X[y == 1]

        def augment_to_target(X_orig, n_target):
            if len(X_orig) >= n_target:
                idx = rng.choice(len(X_orig), n_target, replace=False)
                return X_orig[idx]
            X_result = [X_orig]
            while len(np.vstack(X_result)) < n_target:
                n_needed = n_target - len(np.vstack(X_result))
                idx = rng.choice(len(X_orig), min(len(X_orig), n_needed))
                aug_type = rng.random()
                if aug_type < 0.25:
                    X_aug = X_orig[idx] + rng.normal(0, 0.01, (len(idx), X_orig.shape[1]))
                elif aug_type < 0.5:
                    scale = 1.0 + rng.uniform(-0.03, 0.03, (len(idx), 1))
                    X_aug = X_orig[idx] * scale
                elif aug_type < 0.75:
                    shifts = rng.integers(-20, 20, len(idx))
                    X_aug = np.array([np.roll(X_orig[i], s) for i, s in zip(idx, shifts)])
                else:
                    X_aug = X_orig[idx] * (1.0 + rng.uniform(-0.02, 0.02, (len(idx), 1)))
                    X_aug += rng.normal(0, 0.008, X_aug.shape)
                X_result.append(X_aug)
            return np.vstack(X_result)[:n_target]

        X0_bal = augment_to_target(X0, self.samples_per_class)
        X1_bal = augment_to_target(X1, self.samples_per_class)
        X_bal = np.vstack([X0_bal, X1_bal])
        y_bal = np.concatenate([np.zeros(self.samples_per_class), np.ones(self.samples_per_class)])

        idx = np.arange(len(X_bal))
        rng.shuffle(idx)
        return X_bal[idx], y_bal[idx]

    def load_data(self):
        df = pd.read_csv(self.csv_path)
        flux_cols = [f"flux_{i:04d}" for i in range(self.n_bins)]
        X = df[flux_cols].values
        y = df["label"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
        )
        X_train, y_train = self._create_balanced_dataset(X_train, y_train)

        if self.use_scaler:
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

        return X_train, X_test, y_train, y_test

    def run(self):
        X_train, X_test, y_train, y_test = self.load_data()

        rf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf,
            max_features=self.max_features,
            random_state=self.random_state,
            n_jobs=-1,
            oob_score=True,
        )
        rf.fit(X_train, y_train)
        print(f"OOB Score: {rf.oob_score_:.4f}")

        proba = rf.predict_proba(X_test)[:, 1]
        fpr, tpr, thresholds = roc_curve(y_test, proba)
        best_idx = np.argmax(tpr - fpr)
        best_thresh = thresholds[best_idx]
        y_pred = (proba >= best_thresh).astype(int)

        auc = roc_auc_score(y_test, proba)
        acc = accuracy_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)

        print(f"Optimal threshold (Youden's J): {best_thresh:.4f}")
        print(f"AUC-ROC: {auc:.4f}")
        print(f"Accuracy: {acc:.4f} ({acc * 100:.2f}%)")
        print("\nConfusion Matrix:\n", cm)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=["Non-Planet", "Planet"], digits=4, zero_division=0))

        if self.save_plots:
            os.makedirs(self.output_dir, exist_ok=True)
            self._save_plots(y_test, y_pred, proba, best_thresh)

        if self.save_model:
            os.makedirs(self.output_dir, exist_ok=True)
            joblib.dump(rf, os.path.join(self.output_dir, "tess_rf_model.joblib"))
            np.save(os.path.join(self.output_dir, "rf_optimal_threshold.npy"), best_thresh)

    def _save_plots(self, y_true, y_pred, proba, threshold):
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm, interpolation="nearest")
        fig.colorbar(im, ax=ax)
        ax.set(
            xticks=[0, 1], yticks=[0, 1],
            xticklabels=["Non-Planet", "Planet"], yticklabels=["Non-Planet", "Planet"],
            xlabel="Predicted", ylabel="True",
            title=f"Confusion Matrix (threshold={threshold:.3f})",
        )
        total = cm.sum()
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]}\n({cm[i, j] / total * 100:.1f}%)", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(os.path.join(self.output_dir, "confusion_matrix_rf.png"), dpi=300)
        plt.close(fig)

        # ROC curve
        fpr, tpr, _ = roc_curve(y_true, proba)
        auc = roc_auc_score(y_true, proba)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(fpr, tpr, linewidth=2)
        ax.plot([0, 1], [0, 1], linestyle="--")
        ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title=f"ROC Curve (AUC={auc:.4f})")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(self.output_dir, "roc_curve_rf.png"), dpi=300)
        plt.close(fig)

        # PR curve
        precision, recall, _ = precision_recall_curve(y_true, proba)
        ap = average_precision_score(y_true, proba)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(recall, precision, linewidth=2)
        ax.set(xlabel="Recall", ylabel="Precision", title=f"Precision-Recall Curve (AP={ap:.4f})")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(self.output_dir, "pr_curve_rf.png"), dpi=300)
        plt.close(fig)