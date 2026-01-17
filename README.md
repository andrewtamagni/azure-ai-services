# pulumi-eip-openai-resources

This Azure RM Python Pulumi program deploys all the backend resources necessary to support an Azure OpenAI ChatBot application.  It creates the OpenAI Service with a model deployment, the Search Service, a storage account with container to store the data to be indexed, an Azure Runbook for continuously updating and a Search Index.  All the necessary IAM roles are assigned as well, along with a Log Analytics Workspace that can be configured for logging. All resources are deployed into a new Resource Group.

---

## Third-Party Dependencies

This project uses the following third-party open-source libraries and tools:

- **Pulumi** (Apache-2.0 License) - Infrastructure as Code framework
- **Pulumi Azure Native** (Apache-2.0 License) - Azure provider for Pulumi
- **Azure CLI** (MIT License) - Azure command-line interface

All dependencies are listed in `requirements.txt`. Please refer to each library's license for specific terms and conditions.