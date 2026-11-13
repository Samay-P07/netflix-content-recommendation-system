# Dataset Documentation: Netflix Movies and TV Shows

## 1. Overview & Source
- **Original Source**: Netflix Movies and TV Shows Dataset compiled by Shivam Bansal on [Kaggle](https://www.kaggle.com/datasets/shivamb/netflix-shows).
- **License**: [Creative Commons CC0 1.0 Universal (Public Domain Dedication)](https://creativecommons.org/publicdomain/zero/1.0/).
- **Content Nature**: Catalog-level metadata attributes only. Contains **no** private user identifiers, viewer tracking data, user ratings, or copyrighted video/audio streams.
- **Intended Purpose**: Educational portfolio, algorithmic research, and Information Retrieval demonstrations.
- **Code vs Dataset License**: The project source code is licensed under the MIT License. The dataset is licensed separately under CC0: Public Domain.

---

## 2. Row Counts & Data Integrity
- **Raw CSV Count**: **8,790 records**, 10 columns.
- **Cleaned Canonical Count**: **8,786 unique titles** (after removing 4 duplicate records across `title` and `type` and filtering empty/whitespace-only titles).

### Duplicate Records Resolved During Ingestion
| Title | Format | Release Year | Duplicate Show IDs | Resolution |
| :--- | :--- | :---: | :--- | :--- |
| **9-Feb** | TV Show | 2018 | `s3997`, `s5965` | Deduplicated to canonical entry `s3997` |
| **15-Aug** | Movie | 2019 | `s3963`, `s5967` | Deduplicated to canonical entry `s3963` |
| **22-Jul** | Movie | 2018 | `s4523`, `s5966` | Deduplicated to canonical entry `s4523` |
| **Consequences** | Movie | 2014 | `s3372`, `s6530` | Deduplicated (trailing `\xa0` stripped) |

---

## 3. Data Dictionary
| Column Name | Data Type | Description | Handling in Pipeline |
| :--- | :--- | :--- | :--- |
| `show_id` | String | Unique catalog identifier (e.g. `s1`) | Primary key; preserved for catalog reference. |
| `type` | String | Format indicator (`Movie` or `TV Show`) | Lowercased, converted to token in feature soup; used for format filtering. |
| `title` | String | Official display title | Stripped of whitespace; empty/whitespace titles dropped; indexed for exact, substring, and fuzzy matching. |
| `director` | String | Film director(s) or show creator(s) | Bound into single tokens (e.g., `christopher_nolan`); `'Not Given'`/`'Unknown'` filtered. |
| `country` | String | Country of primary production | Normalized with underscores (e.g., `united_states`); empty strings handled. |
| `date_added` | String | Date added to the streaming service | Informational; excluded from similarity soup. |
| `release_year` | Integer | Original theatrical / broadcast year | Coerced to integer; invalid values imputed with catalog median (2018). |
| `rating` | String | Age maturity rating (TV-MA, PG-13, etc.) | Normalized with underscores (e.g., `tv_ma`); used in metadata soup. |
| `duration` | String | Runtime (e.g. `90 min`, `2 Seasons`) | Displayed in UI; excluded from soup to avoid non-thematic numeric clustering. |
| `listed_in` | String | Comma-separated category & genre tags | Primary content attribute; replicated $2\times$ in metadata soup. |

---

## 4. Setup Instructions if Dataset is Missing
If you clone this repository without `Dataset.csv`:
1. Download `netflix_titles.csv` from the Kaggle dataset page.
2. Rename the file to `Dataset.csv` and place it in this `data/` directory:
   ```
   netflix-content-recommendation-system/
   └── data/
       ├── Dataset.csv
       └── README.md
   ```
3. Run `python main.py` or `streamlit run app.py`—the pipeline will automatically validate and preprocess the catalog.
