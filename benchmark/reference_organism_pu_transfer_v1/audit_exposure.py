"""Audit the fixed PU panel against actual human TRAIN/development only."""
from study_utils import *


if __name__ == '__main__':
    require_container()
    validation = read(OUT/'PANEL_VALIDATION.json')
    require(validation['status']=='passed', 'Panel validation required')
    verify(validation['selection'])
    require(not (OUT/'EXPOSURE_AUDIT.json').exists(), 'Exposure already audited')
    qualified_module('audit_exposure').main()
