"""Apply the qualified TRAIN/development audit to this fixed reference dataset."""
from evaluation_utils import OUT, check_selection, container, qualified_module, require


if __name__ == "__main__":
    container()
    check_selection()
    require(not (OUT / "EXPOSURE_AUDIT.json").exists(), "Refusing to overwrite exposure audit")
    qualified_module("audit_exposure").main()
