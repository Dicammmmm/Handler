import os
import boto3
import logging
import email
import parse
from datetime import datetime
from email import policy
from email.utils import parseaddr

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS client outside the handler
s3 = boto3.client('s3')

# Constants
S3_PROCESSED_PREFIX = 'emails/processed'
NOW = int(datetime.now().timestamp())

# Sender whitelist
SENDERS = {
    'example_brand@example.com': 'ExampleBrand'
}


def lambda_handler(event, context):
    '''
    Main lambda function to handle emails saved in S3 by SES.
    '''

    try:
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        logger.info(f"Triggered by S3 object: s3://{bucket}/{key}")

        # Download raw email content from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_email = response['Body'].read()
        logger.info('Raw email downloaded from S3.')

        # Parse the raw email
        message = email.message_from_bytes(raw_email, policy=policy.default)

    except Exception as e:
        logger.error(f'Failed to extract or parse email from S3: {e}', exc_info=True)
        return error_response('Error reading email from S3.', 500)

    # Extract and validate sender
    sender_email = get_sender_email(message)
    if sender_email not in SENDERS:
        logger.warning(f"Sender '{sender_email}' not found in whitelist. Skipping.")
        return success_response('Sender not in whitelist.')

    brand = SENDERS[sender_email]
    logger.info(f'Processing attachments for brand: {brand}')

    # Main processing logic
    for filename, df in process_attachments(message, brand):
        try:
            json_key = f"{S3_PROCESSED_PREFIX}/{os.path.splitext(filename)[0]}_{NOW}.json" # File destination
            write_to_s3(bucket, json_key, df) # Writing to S3 at the above specified destination
            logger.info(f'Saved parsed JSON to: s3://{bucket}/{json_key}')

        except Exception as e:
            logger.error(f"Failed to save parsed file for {filename}: {e}", exc_info=True)

    return success_response('Email processed successfully.')


def process_attachments(msg, brand):
    '''
    Generator that yields (filename, parsed DataFrame) for each attachment.
    '''

    # Check if there is an attachment in the email
    if not msg.is_multipart():
        logger.info('Email is not multipart. No attachments.')
        return

    # Load the attachment into a variable
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if not filename:
            logger.warning('Attachment missing filename. Skipping.')
            continue

        content = part.get_payload(decode=True)
        if not content:
            logger.warning(f'No content found in attachment: {filename}. Skipping.')
            continue

        # Process the brands attachment
        try:
            match brand:
                case 'ExampleBrand':
                    df = parse.examplebrand(content)
                case _:
                    logger.warning(f'Unrecognized brand: {brand}. Skipping.')
                    continue

            yield filename, df

        except Exception as e:
            logger.error(f'Failed to parse attachment {filename}: {e}', exc_info=True)
            continue


def get_sender_email(msg):
    raw_sender = msg.get('From', '')
    sender = parseaddr(raw_sender)[1].lower()
    logger.debug(f'Processing sender: {sender}')
    return sender


def write_to_s3(bucket, key, df):
    json_str = df.to_json(orient='records', lines=True)
    s3.put_object(Bucket=bucket, Key=key, Body=json_str, ContentType='application/json')


def success_response(message):
    return {'statusCode': 200, 'body': message}


def error_response(message, code=500):
    return {'statusCode': code, 'body': message}
