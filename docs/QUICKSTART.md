# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/bagley.git
cd bagley

# Install dependencies
pip install -r requirements.txt
```

## Running Bagley

### Option 1: Using the helper script (recommended)
```bash
./run.sh
```

### Option 2: Manual execution
```bash
PYTHONPATH=. python3 tools/cli.py
```

## Basic Commands

### List available lab types
```
h4ch1@orchestrator> list
```

### Start a lab
```
h4ch1@orchestrator> start dvwa
```

### Check status
```
h4ch1@orchestrator> status
```

### Stop a lab
```
h4ch1@orchestrator> stop dvwa
```

### Delete a lab
```
h4ch1@orchestrator> delete dvwa
```

## Testing

Run the test suite:
```bash
python3 tests/test_orchestrator.py
```

## Enabling AI Features (Optional)

1. Get an OpenRouter API key from https://openrouter.ai
2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your key:
   ```
   OPENROUTER_API_KEY=your-actual-key-here
   ```
4. Load the environment:
   ```bash
   source .env  # or export OPENROUTER_API_KEY=...
   ```

With AI enabled, you can use natural language:
```
h4ch1@orchestrator> I need a DVWA instance
h4ch1@orchestrator> What labs do I have running?
```

## Troubleshooting

### ModuleNotFoundError: No module named 'skills'
Make sure you're running from the project root and using `./run.sh` or setting `PYTHONPATH=.`

### python: command not found
Use `python3` instead of `python`

### AI features not working
- Verify your API key is set: `echo $OPENROUTER_API_KEY`
- Check you have internet connectivity
- Verify the `requests` package is installed: `pip list | grep requests`
