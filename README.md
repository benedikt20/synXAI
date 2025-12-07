# synXAI
Synergistic Explanations for Neural Networks.

Note that the training data is not included in this repo due to NDA restrictions. All notebooks include outputs of cells that shows the training process and results.


## Folder structure:
- `data_prep_notebooks/`: Notebooks for preparing and augmenting the data (need to be moved out of this folder to execute). Just data preparation.
- `rawdata/`: Raw data files (not included in repo due to size and NDA restrictions).
- `data/`: Processed data files (generated automatically by data preparation notebooks, not included due to NDA restrictions).
- `src/`: Source files to the data preparation.

## Files:
- `download_config.yaml`: Configuration file for downloading environmental data, including spatial and temporal boundaries.
- `nn_classifier.ipynb`: Main notebook, training the MLP classifier and generating explanations with SynXAI.
- `baselines.ipynb`: Notebook containing baseline models to compare against performance of the MLP. 