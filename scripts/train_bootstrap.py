"""
Script de treinamento do Bootstrap Classifier.

Utiliza detect_settings para caminhos e hiperparâmetros,
garantindo coesão com o restante do projeto.

Uso:
    python -m scripts.train_bootstrap
    python -m scripts.train_bootstrap --epochs 50 --batch-size 32
    python -m scripts.train_bootstrap --data-dir data/custom --unfreeze-epoch 15
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, random_split
    from torchvision import datasets, models, transforms
except ImportError:
    print(
        "Dependencias de treinamento nao instaladas.\n"
        "Execute: pip install torch torchvision"
    )
    sys.exit(1)

from src.detect.config import detect_settings
from src.monitoring.prediction_logger import PredictionLogger
from src.monitoring.alert_manager import AlertManager
from src.monitoring.models import AlertSeverity

# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms(phase: str, tile_size: int) -> transforms.Compose:
    """Retorna transforms de treino ou validação baseados no tile_size do config."""
    if phase == "train":
        return transforms.Compose([
            transforms.Resize((tile_size, tile_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
            transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize((tile_size, tile_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

def build_model(num_classes: int = 2, freeze_backbone: bool = True) -> nn.Module:
    """Constrói ResNet18 com head customizado para classificação binária."""
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(128, num_classes),
    )

    return model


# ---------------------------------------------------------------------------
# Treino e avaliação
# ---------------------------------------------------------------------------

def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    """Executa uma epoch de treino. Retorna (loss, accuracy)."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / max(total, 1)
    epoch_acc = correct / max(total, 1)
    return epoch_loss, epoch_acc


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    """Avalia o modelo no conjunto de validação. Retorna (loss, accuracy)."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / max(total, 1)
    epoch_acc = correct / max(total, 1)
    return epoch_loss, epoch_acc


# ---------------------------------------------------------------------------
# Validações pré-treino
# ---------------------------------------------------------------------------

def validate_data_dir(data_dir: Path) -> list[str]:
    """Verifica se o diretório de dados está estruturado corretamente."""
    errors: list[str] = []

    if not data_dir.exists():
        errors.append(f"Diretorio '{data_dir}' nao encontrado.")
        return errors

    subdirs = [d.name for d in data_dir.iterdir() if d.is_dir()]
    if len(subdirs) < 2:
        errors.append(
            f"Esperadas pelo menos 2 subpastas de classes, encontradas: {subdirs}"
        )
        return errors

    for subdir_name in subdirs:
        subdir = data_dir / subdir_name
        images = list(subdir.glob("*"))
        image_files = [
            f for f in images
            if f.suffix.lower() in detect_settings.allowed_extensions
        ]
        if len(image_files) < 10:
            errors.append(
                f"Classe '{subdir_name}' tem apenas {len(image_files)} imagens "
                f"(minimo recomendado: 10)."
            )

    return errors


# ---------------------------------------------------------------------------
# Integração com monitoring
# ---------------------------------------------------------------------------

def notify_training_complete(
    best_acc: float,
    total_epochs: int,
    output_path: Path,
) -> None:
    """Dispara alerta no monitoring ao concluir o treinamento."""
    try:
        alert_manager = AlertManager()
        alert_manager.fire(
            title="Treinamento bootstrap concluido",
            message=(
                f"Modelo salvo em {output_path} | "
                f"best_val_acc={best_acc:.4f} | epochs={total_epochs}"
            ),
            severity=AlertSeverity.INFO,
            source="train_bootstrap",
        )
    except Exception:
        pass  # Monitoring indisponível não deve interromper o script


def log_training_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    class_names: list[str],
) -> None:
    """Registra predições do modelo final no PredictionLogger para baseline de drift."""
    try:
        logger = PredictionLogger()
        model.eval()
        softmax = nn.Softmax(dim=1)

        with torch.no_grad():
            for inputs, labels in loader:
                inputs = inputs.to(device)
                outputs = softmax(model(inputs))
                confidences, predicted = outputs.max(1)

                for conf, pred, label in zip(
                    confidences.cpu().tolist(),
                    predicted.cpu().tolist(),
                    labels.tolist(),
                ):
                    logger.log(
                        confidence=conf,
                        predicted_class=class_names[pred],
                        true_class=class_names[label],
                        source="train_bootstrap",
                    )
    except Exception:
        pass  # Logging indisponível não deve interromper o script


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parseia argumentos CLI com defaults vindos de detect_settings."""
    bootstrap_model_path = Path(detect_settings.bootstrap_model_path)

    parser = argparse.ArgumentParser(
        description="Treinar Bootstrap Classifier — Identificação Aérea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/bootstrap",
        help="Diretorio com subpastas por classe (positives/, negatives/)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(bootstrap_model_path),
        help="Caminho de saida do modelo .pth",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Numero maximo de epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Tamanho do batch",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
        help="Learning rate inicial",
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Fracao do dataset para validacao (0.0 a 1.0)",
    )
    parser.add_argument(
        "--unfreeze-epoch",
        type=int,
        default=10,
        help="Epoch a partir da qual desbloqueia o backbone para fine-tuning",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=7,
        help="Epochs sem melhoria antes do early stopping",
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=detect_settings.tile_size,
        help="Tamanho do tile (resize das imagens)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed para reproducibilidade",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # --- Reproducibilidade ---
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # --- Paths ---
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Validação dos dados ---
    print("=" * 60)
    print("  Identificação Aérea — Bootstrap Classifier Training")
    print("=" * 60)

    errors = validate_data_dir(data_dir)
    if errors:
        print("\n[ERRO] Problemas no diretorio de dados:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # --- Device ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice:     {device}")
    print(f"Tile size:  {args.tile_size}")
    print(f"Output:     {output_path}")
    print(f"Seed:       {args.seed}")

    # --- Dataset ---
    full_dataset = datasets.ImageFolder(
        str(data_dir),
        transform=get_transforms("train", args.tile_size),
    )
    class_names = full_dataset.classes
    num_classes = len(class_names)

    print(f"Classes:    {class_names}")
    print(f"Imagens:    {len(full_dataset)}")

    # Class balance check
    class_counts = {}
    for _, label in full_dataset.samples:
        name = class_names[label]
        class_counts[name] = class_counts.get(name, 0) + 1
    print("Distribuicao:")
    for cls, count in class_counts.items():
        pct = count / len(full_dataset) * 100
        print(f"  {cls}: {count} ({pct:.1f}%)")

    # --- Split ---
    val_size = int(len(full_dataset) * args.val_split)
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(args.seed),
    )

    # Transforms de validação (sem augmentation)
    val_transform_dataset = datasets.ImageFolder(
        str(data_dir),
        transform=get_transforms("val", args.tile_size),
    )
    val_dataset.dataset = val_transform_dataset

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=device.type == "cuda",
    )

    print(f"Treino:     {train_size}")
    print(f"Validacao:  {val_size}")
    print(f"Batches:    {len(train_loader)} train / {len(val_loader)} val")
    print("-" * 60)

    # --- Modelo ---
    model = build_model(num_classes=num_classes, freeze_backbone=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3, verbose=True,
    )

    # --- Training loop ---
    best_val_acc = 0.0
    patience_counter = 0
    history: list[dict] = []

    for epoch in range(args.epochs):
        current_lr = optimizer.param_groups[0]["lr"]

        # Unfreeze backbone
        if epoch == args.unfreeze_epoch:
            print(f"\n>> Epoch {epoch + 1}: desbloqueando backbone (fine-tuning)")
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.Adam(model.parameters(), lr=current_lr * 0.1)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="max", factor=0.5, patience=3, verbose=True,
            )

        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device,
        )
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        scheduler.step(val_acc)

        history.append({
            "epoch": epoch + 1,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "lr": round(optimizer.param_groups[0]["lr"], 8),
        })

        marker = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_names": class_names,
                    "num_classes": num_classes,
                    "val_acc": best_val_acc,
                    "epoch": epoch + 1,
                    "tile_size": args.tile_size,
                    "confidence_threshold": detect_settings.confidence_threshold,
                    "args": vars(args),
                },
                output_path,
            )
            marker = " ✓ salvo"
        else:
            patience_counter += 1

        print(
            f"Epoch {epoch + 1:3d}/{args.epochs} | "
            f"Train {train_loss:.4f} / {train_acc:.4f} | "
            f"Val {val_loss:.4f} / {val_acc:.4f} | "
            f"LR {optimizer.param_groups[0]['lr']:.6f} | "
            f"P {patience_counter}/{args.patience}{marker}"
        )

        if patience_counter >= args.patience:
            print(f"\n>> Early stopping na epoch {epoch + 1}")
            break

    # --- Métricas finais ---
    print("-" * 60)
    print(f"Melhor val_acc: {best_val_acc:.4f}")

    metrics_path = output_path.parent / "training_metrics.json"
    metrics = {
        "project": "Identificacao Aerea",
        "script": "train_bootstrap",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "device": str(device),
        "best_val_acc": round(best_val_acc, 4),
        "total_epochs": len(history),
        "early_stopped": patience_counter >= args.patience,
        "class_names": class_names,
        "class_distribution": class_counts,
        "dataset_size": len(full_dataset),
        "train_size": train_size,
        "val_size": val_size,
        "tile_size": args.tile_size,
        "confidence_threshold": detect_settings.confidence_threshold,
        "detect_settings": {
            "nms_iou_threshold": detect_settings.nms_iou_threshold,
            "mock_inference": detect_settings.mock_inference,
        },
        "args": vars(args),
        "history": history,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Metricas:   {metrics_path}")
    print(f"Modelo:     {output_path}")

    # --- Integração monitoring ---
    if best_val_acc > 0:
        print("\nRegistrando predicoes no monitoring para baseline de drift...")
        best_checkpoint = torch.load(output_path, map_location=device, weights_only=False)
        model.load_state_dict(best_checkpoint["model_state_dict"])
        log_training_predictions(model, val_loader, device, class_names)
        notify_training_complete(best_val_acc, len(history), output_path)
        print("Concluido.")

    print("=" * 60)


if __name__ == "__main__":
    main()
