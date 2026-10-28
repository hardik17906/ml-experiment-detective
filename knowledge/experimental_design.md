Title: Common pitfalls and recommended practices
URL: https://scikit-learn.org/stable/common_pitfalls.html
Topic: experimental design, data leakage and generalization
Source-Type: official documentation (scikit-learn), paraphrase verified 2026-10-28
Text:
Data leakage can make estimated model performance overly optimistic. Split data before learning preprocessing parameters, fit transformations on training data, and apply the learned transformations consistently to held-out data. Test data should not guide model choices. Control randomness deliberately and record how data and models were configured. Our application therefore uses one recorded validation split from the training partition and keeps the official test partition outside proposal selection. Repeated validation-guided choices can still adapt to that validation set; a controlled pair alone does not establish a general causal explanation.
