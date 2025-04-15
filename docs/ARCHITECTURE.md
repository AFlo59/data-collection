```
data-collection/
├── logs/                    # Log files directory
│   └── data_extraction/     # Specific logs for data extraction
│       ├── run/     # Specific logs for data extraction/ run+spiders
│       └── tests/     # Specific logs for data extraction/ tests
├── docs/                    # Documentation in Markdown
├── setup/                   # Setup and environment scripts
├── src/                     # Source code
│   ├── data_extraction/     # Data extraction module
│   │   └── spiders/        # Individual scrapers
│   │   └── run/        # run Individual scrapers
│   │   └── tests/        # test Individual scrapers
│   └── utils/             # Utility functions
│       └── setup_logger.py        # script pour creer le folder logs à la racine , les subfolder, et les log
└── data/                   # Data storage
    └── scraping/           # Scraped data storage
```