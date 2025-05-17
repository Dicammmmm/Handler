# Email Attachment Processor

This project automates the processing of email attachments using AWS services. It receives emails through AWS SES, stores them in S3, processes their attachments with AWS Lambda, and converts them into standardized JSON format for further analysis.

## Architecture Overview

```
                     ┌───────────┐                  ┌───────────┐
                     │           │                  │           │
Sender ──────────────►   SES     ├─────────────────►│    S3     │
                     │           │                  │           │
                     └───────────┘                  └─────┬─────┘
                                                          │
                                                          │
                                                          │
                                                          ▼
                                                    ┌───────────┐
                                                    │           │
                                                    │  Lambda   │
                                                    │           │
                                                    └─────┬─────┘
                                                          │
                                                          │
                                                          │
                                                          ▼
                                                    ┌───────────┐
                                                    │ Processed │
                                                    │  Files    │
                                                    │    S3     │
                                                    └───────────┘
```

## How it Works

1. **Email Reception (AWS SES & Route 53)**:
   - Route 53 manages the DNS records for your domain
   - AWS SES receives emails sent to specified email addresses
   - Incoming emails are automatically saved to an S3 bucket

2. **Email Storage (AWS S3)**:
   - Raw emails are stored in the configured S3 bucket
   - This triggers the Lambda function

3. **Processing Pipeline (AWS Lambda)**:
   - Lambda function is triggered by new email objects in S3
   - The function:
     - Verifies the sender is in the whitelist
     - Extracts attachments from the email
     - Processes attachments based on the sender's brand
     - Converts data to a standardized format
     - Saves the processed data as JSON in the S3 bucket

4. **Data Storage**:
   - Processed data is stored in a standardized JSON format
   - Files are saved to the `emails/processed` prefix in the S3 bucket
   - Filenames include the original name and a timestamp

## Project Components

### `email_handler.py`

The main Lambda function that:
- Receives S3 event notifications
- Downloads and parses emails
- Validates senders against a whitelist
- Processes attachments using brand-specific parsers
- Saves processed data to S3

### `parse.py`

Contains utilities for parsing and standardizing attachment data:
- `get_attachment()`: Attempts to read the attachment as CSV or Excel
- `standardize_columns()`: Normalizes column names and adds timestamps
- Brand-specific parsing functions (e.g., `examplebrand()`)

## Configuration

### Sender Whitelist

The system only processes emails from approved senders defined in the `SENDERS` dictionary:

```python
SENDERS = {
    'example_brand@example.com': 'ExampleBrand'
}
```

To add more senders, update this dictionary with the sender's email and corresponding brand identifier.

### AWS Setup Required

1. **Route 53**:
   - Set up your domain and MX records to direct emails to SES

2. **SES (Simple Email Service)**:
   - Verify your domain
   - Configure receipt rules to store emails in S3

3. **S3 (Simple Storage Service)**:
   - Create a bucket for storing raw emails and processed data
   - Configure bucket notifications to trigger Lambda

4. **Lambda**:
   - Deploy the Lambda function with the code from this repository
   - Configure appropriate IAM roles with permissions for S3 access
   - Set up the S3 trigger for your email bucket

## Adding New Brand Parsers

To support a new email sender:

1. Add the sender's email to the `SENDERS` dictionary in `email_handler.py`
2. Create a new parsing function in `parse.py` for the brand
3. Update the `process_attachments` function's match case to handle the new brand

Example:

```python
# In parse.py
def newbrand(data):
    df = get_attachment(data)
    # Brand-specific transformations
    df = standardize_columns(df)
    return df

# In email_handler.py
match brand:
    case 'ExampleBrand':
        df = parse.examplebrand(content)
    case 'NewBrand':
        df = parse.newbrand(content)
    case _:
        logger.warning(f'Unrecognized brand: {brand}. Skipping.')
        continue
```

## Development and Deployment

### Local Development

1. Clone the repository
2. Install dependencies: `pip install boto3 pandas`
3. Set up AWS credentials locally

### Deployment

1. Package the code and dependencies
2. Deploy to AWS Lambda using the AWS Management Console, AWS CLI, or other deployment tools
3. Configure the necessary AWS services as outlined in the AWS Setup section

## Logging

The system uses AWS CloudWatch for logging:
- Debug-level logging for detailed processing information
- Info-level logging for general operation steps
- Warning and error logging for issues

## Requirements

- Python 3.10+
- boto3
- pandas
