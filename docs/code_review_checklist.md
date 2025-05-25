# Code Review Checklist

This checklist is designed to help reviewers evaluate code changes consistently and thoroughly. It includes general code quality checks as well as specific considerations for AI-assisted development.

## General Code Quality

- [ ] Code follows PEP 8 style guidelines
- [ ] Variable and function names are clear and descriptive
- [ ] Functions have appropriate docstrings with parameter descriptions
- [ ] Type hints are used consistently
- [ ] Error handling is appropriate and comprehensive
- [ ] Edge cases are considered and handled
- [ ] No unnecessary code duplication
- [ ] Code is efficient and optimized where appropriate
- [ ] Logging is used appropriately
- [ ] Tests are included for new functionality
- [ ] Existing tests pass with the changes

## API-Specific Checks

- [ ] API contracts are maintained
- [ ] Request and response structures match API requirements
- [ ] Field names and data types are correct
- [ ] Authentication is handled properly
- [ ] Error responses are handled appropriately
- [ ] Backward compatibility is maintained
- [ ] API documentation is updated if necessary

## AI-Assisted Development Checks

- [ ] AI-safe markers are preserved and respected
- [ ] Critical code sections are not modified inappropriately
- [ ] Changes to API-related code maintain required structures
- [ ] AI-generated code follows project standards
- [ ] AI-suggested changes are reviewed with extra scrutiny
- [ ] Documentation reflects any AI-assisted changes
- [ ] Tests verify that API interactions still work correctly

## Security Considerations

- [ ] No sensitive information is exposed
- [ ] Input validation is performed
- [ ] Authentication and authorization are handled securely
- [ ] No potential injection vulnerabilities
- [ ] Rate limiting and throttling are considered

## Documentation

- [ ] Code changes are well-documented
- [ ] README is updated if necessary
- [ ] API documentation is updated if necessary
- [ ] Examples are updated if necessary
- [ ] Changelog is updated if necessary

## Testing

- [ ] Unit tests cover the changes
- [ ] Integration tests verify API interactions
- [ ] Edge cases are tested
- [ ] Error cases are tested
- [ ] Tests are clear and maintainable

## Final Checks

- [ ] Code is ready for production
- [ ] No debugging code or commented-out code
- [ ] No TODOs without corresponding issues
- [ ] All review comments are addressed
- [ ] CI/CD pipeline passes

## AI-Modified Critical Sections

If changes involve critical API sections marked with AI-safe markers:

- [ ] Changes maintain the exact field names required by the API
- [ ] Data structures match API requirements
- [ ] Changes are tested with actual API interactions
- [ ] Documentation is updated to reflect changes
- [ ] Extra review attention is given to these sections

## Reviewer Notes

Use this section to add any specific notes or concerns about the code changes:

- 
- 
- 

## Approval

- [ ] Approved without changes
- [ ] Approved with minor changes requested
- [ ] Changes required before approval
- [ ] Rejected (provide reason in notes)
