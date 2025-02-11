FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies for OpenCV
RUN yum install -y \
    gcc \
    gcc-c++ \
    cmake3 \
    mesa-libGL \
    && yum clean all

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install Python dependencies
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY src/ ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "main.handler" ]