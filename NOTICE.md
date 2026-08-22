# Data attribution

## CMMC 2.0 / NIST SP 800-171 Compliance QA Corpus

`dataset/cmmc_train.json` and `dataset/cmmc_validation.json` are redistributed from:

> Memoriant, Inc. (2026). *CMMC 2.0 / NIST SP 800-171 compliance QA corpus* [Data set].
> Hugging Face. https://huggingface.co/datasets/memoriant/cmmc-training-data-2026-q2

Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0):
https://creativecommons.org/licenses/by/4.0/

The PDFs in `tprm_app/documents_from_the_business/` are a derivative of that corpus,
produced by `tprm_app/build_corpus.py`, and are redistributed under the same licence.
No changes were made to the substance of the answer text; the script groups answers by
NIST control family and typesets them as PDFs.

## Source standards

The corpus content derives from publicly available U.S. federal publications,
including NIST SP 800-171, NIST SP 800-53, CMMC 2.0 model documentation, and the
CISA Known Exploited Vulnerabilities catalogue. Works of the U.S. federal government
are not subject to copyright protection in the United States.

## Code

Copyright (c) 2026 Sam Olamazadeh. All rights reserved.

The code is published so that the experiment reported in the Major Research
Project can be examined and reproduced. No licence to reuse, modify, or
redistribute it is granted. The CC BY 4.0 terms set out above apply to the data
files, not to the code.
