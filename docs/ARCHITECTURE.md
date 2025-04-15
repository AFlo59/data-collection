```
data-collection/
├── logs/                    # Log files directory
│   └── data-extraction/     # Specific logs for data extraction
├── docs/                    # Documentation in Markdown
├── setup/                   # Setup and environment scripts
├── src/                     # Source code
│   ├── data-extraction/     # Data extraction module
│   │   └── spiders/        # Individual scrapers
│   ├── run-extraction/     # run individual scrapers
│   ├── tests-extraction/     # test individual scrapers
│   └── utils/             # Utility functions
│       └── setup_logger.py        # script pour creer le folder logs à la racine , les subfolder, et les log
└── data/                   # Data storage
    └── scraping/           # Scraped data storage
```