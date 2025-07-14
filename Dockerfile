FROM public.ecr.aws/lambda/python:3.12

COPY src ${LAMBDA_TASK_ROOT}
COPY rules.json ${LAMBDA_TASK_ROOT}/code_review
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt
