# TheMITbro Formatter Architecture

The formatter is organized as a publishing pipeline rather than a single formatting script.

```text
Raw Question / Question Paper
            |
            v
       Processor
            |
            v
   Math Normalization
            |
            v
      Question IR
            |
            v
       Validation
            |
            +-------------------+
            |                   |
            v                   v
      Layout Engine       Diagram Engine
            |                   |
            +---------+---------+
                      |
                      v
               Render / Export
                 /    |    \
                v     v     v
             Markdown SVG  PDF / HTML
```

## Stability boundary

The public API and the build/input contracts established in M25/M26 are treated as release boundaries. Later milestones should extend behavior without silently changing those contracts.
