# Dynamic Pre-commit Hook Generator

This tool uses Google's Gemini LLM to analyze your codebase and generate customized pre-commit hooks based on your project's specific needs.

## Features

- **Codebase Analysis**: Analyzes your codebase to identify file types, dependencies, and existing configurations
- **CI/CD Integration**: Aligns pre-commit hooks with your CI/CD workflows
- **Custom Hooks**: Creates custom hooks for checking documentation freshness
- **Non-interactive Mode**: Supports automation in CI/CD pipelines
- **Fallback Mechanisms**: Provides robust error handling with fallback configurations

## Usage

### Basic Usage

```bash
python3 scripts/dynamic_precommit_generator.py
```

This will analyze your codebase, generate a customized pre-commit configuration, and prompt for confirmation before applying changes.

### Non-interactive Mode

```bash
python3 scripts/dynamic_precommit_generator.py --non-interactive
```

This will generate and apply changes without prompting for confirmation, ideal for automation.

### Additional Options

```bash
python3 scripts/dynamic_precommit_generator.py --non-interactive --install
```

The `--install` flag will automatically install the hooks after generating the configuration.

## Requirements

- Python 3.6+
- `google-generativeai` package
- `python-dotenv` package
- `pyyaml` package
- Google Gemini API key (set as `GOOGLE_GEMINI_API_KEY` environment variable)

## Configuration

The generator uses the following environment variables:

- `GOOGLE_GEMINI_API_KEY`: Your Google Gemini API key

You can set these in a `.env` file in the project root.

## Expected Behavior

The generator should:

1. Analyze your codebase to identify file types, dependencies, and existing configurations
2. Analyze your CI/CD workflows to ensure alignment
3. Generate a customized pre-commit configuration based on this analysis
4. Create custom hooks for checking documentation freshness
5. Apply changes (with confirmation in interactive mode)
6. Install hooks if requested

## Known Issues and Edge Cases

| Issue | Description | Workaround |
|-------|-------------|------------|
| API Rate Limiting | Google Gemini API may rate limit requests | Run the generator less frequently or use fallback mode |
| Large Codebases | Analysis may be slow for very large codebases | Run on a subset of the codebase or use fallback mode |
| Custom Hook Limitations | Generated custom hooks may not handle all edge cases | Manually review and adjust generated hooks |
| Model Hallucinations | LLM may occasionally generate invalid YAML | The generator validates YAML and falls back to a basic config if invalid |
| Dependency Conflicts | Generated hooks may have conflicting dependencies | Manually resolve conflicts in the generated config |

## Troubleshooting

### API Key Issues

If you see warnings about the API key:

```
Warning: GOOGLE_GEMINI_API_KEY not set
Some features will be limited to fallback implementations
```

Make sure you've set the `GOOGLE_GEMINI_API_KEY` environment variable or added it to your `.env` file.

### Invalid YAML

If the generator produces invalid YAML, it will fall back to a basic configuration. You can manually adjust the configuration after generation.

### Custom Hook Issues

If the custom hooks don't work as expected, you can manually edit them in the `.pre-commit-hooks` directory.

## Contributing

When making changes to the generator:

1. Document any new edge cases or issues in this README
2. Add fallback mechanisms for new features
3. Test both interactive and non-interactive modes
4. Ensure backward compatibility with existing configurations

### Modifying Pre-commit Configuration

When modifying the `.pre-commit-config.yaml` file or adding new hooks:

1. Use `git commit --no-verify` when committing changes to the pre-commit configuration itself
2. This bypasses the pre-commit hooks, which is necessary when adding new hooks that aren't installed yet
3. After committing, run `pre-commit install` to install the new hooks
4. Future commits can then be made normally without `--no-verify`

```bash
# Example workflow when modifying pre-commit configuration
git add .pre-commit-config.yaml
git commit -m "Add new pre-commit hooks" --no-verify
pre-commit install  # Install the new hooks
```

> **Note:** Using `--no-verify` should be limited to cases where you're modifying the pre-commit infrastructure itself. For normal development, always let the hooks run to ensure code quality.

## Future Development

This tool is being battle-tested within this project before potentially being extracted as a standalone package. See issue #107 for more details.
