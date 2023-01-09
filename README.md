# F22 Raptor - AWS Asset Inventory 
F22 Raptor asset targets the Organizations whose businesses are hosted on AWS. This asset project provides a dashboard for cloud administrators, managers, IT admins etc to monitor their resources via who created and when the resource was created. Furthermore the administrators will be able to export the report in PDF and csv format, along with these reports can directly be sent to the respective stakeholders. 

## UX Design
A GuardDuty finding represents a potential security issue detected within the network. GuardDuty generates a finding whenever it detects unexpected and potentially malicious activity in your AWS environment.

## Database Design

## API Design 

## Technology Architecture Design 
![Work-Flow Diagram](https://github.com/roshangami/aws_threat_prevention/blob/master/images/DFD-guardDuty.png "Threat detection and remediation diagram")

The project is created in classical AWS  3 tier application development structure. The front end tier is hosted in AWS EC2 instance. 
Second tier is basically the backend servers where the request from front end servers are forwarded to API Gateway and processed at AWS Lambda function.  
Third tier is the database where Dynamodb is used to store all the data. 

The below diagram explains how the tool is able to gather information
![Work-Flow Diagram](https://github.com/roshangami/aws_threat_prevention/blob/master/images/DFD-guardDuty.png "Threat detection and remediation diagram")

We have 2 AWS accounts, the F22 Raptor is the service account and the first box in the diagram is the customer AWS account. 
In the customer AWS account we just need to create one IAM role with a set of read only permissions for various AWS services.  
Now in the AWS service account (F22 Raptor) that role just need to be assumed and attached to the lambda which is responsible for collecting  the required info from the customer account. 


## Tools and Technologies 
![tools](https://github.com/roshangami/aws_threat_prevention/blob/master/images/DFD-guardDuty.png "Threat detection and remediation diagram")
 

## Author 
Roshan Gami
