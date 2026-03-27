#!/bin/bash

# --- CONFIGURATION ---
ROLE_NAME="FeedbackAnalyzerRole"
BUCKET_NAME="comp264-edwin-1772030214"
REGION="us-east-1"
FUNCTION_NAME="ocr_worker"

echo "🔐 1. Attaching S3 and Textract Permissions to $ROLE_NAME..."
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name S3TextractAccess \
  --region $REGION \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::'$BUCKET_NAME'",
                "arn:aws:s3:::'$BUCKET_NAME'/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": ["textract:DetectDocumentText"],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["dynamodb:PutItem", "dynamodb:GetItem"],
            "Resource": "arn:aws:dynamodb:'$REGION':*:table/Analysis_OCR"
        },
        {
            "Effect": "Allow",
            "Action": ["lambda:InvokeFunction"],
            "Resource": "arn:aws:lambda:'$REGION':*:function:summary_worker"
        }
    ]
}'

echo "🤝 2. Ensuring S3 has permission to trigger $FUNCTION_NAME..."
aws lambda add-permission \
  --function-name $FUNCTION_NAME \
  --statement-id s3-trigger-permission \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$BUCKET_NAME \
  --region $REGION || echo "⚠️ Permission already exists, skipping..."

echo "⏳ Waiting 10 seconds for AWS IAM propagation..."
sleep 10

echo "🚀 3. Running Final Validation Test (ID: admin_6cfd607a)..."
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --payload "$(echo '{
    "Records": [
      {
        "s3": {
          "bucket": { "name": "'$BUCKET_NAME'" },
          "object": { "key": "uploads/admin_6cfd607a.jpg" }
        }
      }
    ]
  }' | base64)" \
  response.json && cat response.json

echo -e "\n\n✅ Done! Check the JSON above. If it says 'success', your cloud is fixed."