"""
This Azure RM Python Pulumi program deploys all the backend resources necessary to support an
Azure OpenAI ChatBot application.  It creates the OpenAI Service with a model deployment, the
Search Service, a storage account with container to store the data to be indexed, an Azure
Runbook for continuously updating and a Search Index.  All the necessary IAM roles are assigned
as well, along with a Log Analytics Workspace that can be configured for logging. All resources
are deployed into a new Resource Group.
"""

import pulumi
from pulumi_azure_native import resources, storage, search, cognitiveservices, authorization, automation, operationalinsights
from default_vars import *

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(str(prefix) + "-AI",
    resource_group_name=str(prefix) + "-AI",
    tags={'createdBy': 'Pulumi'},
)

# Create Log Analytics Workspace
log_analytics_workspace = operationalinsights.Workspace(str(prefix.lower()) + "-ai-logs",
    workspace_name=str(prefix.lower()) + "-ai-logs",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=operationalinsights.WorkspaceSkuArgs(
        name="PerGB2018"
    ),
    retention_in_days=30,
    tags={'createdBy': 'Pulumi'},
    opts=pulumi.ResourceOptions(depends_on=[resource_group])
)

# OpenAI Service
cognitive_account = cognitiveservices.Account(str(prefix.lower()) + "-ai-service",
    account_name=str(prefix.lower()) + "-ai-service",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    tags={'createdBy': 'Pulumi'},
    sku=cognitiveservices.SkuArgs(
        name='S0',
    ),
    kind='OpenAI',
    properties=cognitiveservices.AccountPropertiesArgs(
        custom_sub_domain_name=str(prefix.lower()) + "-ai-service",
        public_network_access='Enabled',
    ),
    identity=cognitiveservices.IdentityArgs(
        type='SystemAssigned', 
    ),
    opts=pulumi.ResourceOptions(depends_on=[resource_group])
)
"""
# GPT 4o OpenAI Model Deployment
gpt_4o_deployment = cognitiveservices.Deployment(
    'gpt_4o_deployment',
    account_name=str(prefix.lower()) + "-ai-service",
    deployment_name='gpt-4o',
    resource_group_name=resource_group.name,
    sku=cognitiveservices.SkuArgs(
        name='Standard',
        capacity=70,
    ),
    properties=cognitiveservices.DeploymentPropertiesArgs(
        model=cognitiveservices.DeploymentModelArgs(
            format='OpenAI',
            name='gpt-4o',
            version='2024-05-13',
        ),
        version_upgrade_option='OnceNewDefaultVersionAvailable',
        rai_policy_name="Microsoft.Default",
    ),
    opts=pulumi.ResourceOptions(depends_on=[cognitive_account])
)
"""
# GPT 5 Pro OpenAI Model Deployment
gpt_5_1_deployment = cognitiveservices.Deployment(
    'gpt_5.1_deployment',
    account_name=str(prefix.lower()) + "-ai-service",
    deployment_name='gpt-5.1',
    resource_group_name=resource_group.name,
    sku=cognitiveservices.SkuArgs(
        name='Standard',
        capacity=70,
    ),
    properties=cognitiveservices.DeploymentPropertiesArgs(
        model=cognitiveservices.DeploymentModelArgs(
            format='OpenAI',
            name='gpt-5.1',
            version='2025-11-13',
        ),
        version_upgrade_option='OnceNewDefaultVersionAvailable',
        rai_policy_name="Microsoft.Default",
    ),
    opts=pulumi.ResourceOptions(depends_on=[cognitive_account])
)

# AI Search Service
search_service = search.Service(str(prefix.lower()) + "-ai-search",
    search_service_name=str(prefix.lower()) + "-ai-search",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=search.SkuArgs(
        name='basic'
    ),
    replica_count=1,
    partition_count=1,
    hosting_mode="Default",
    public_network_access="Enabled",
    identity=search.IdentityArgs(
        type="SystemAssigned"
    ),
     auth_options={
        "aadOrApiKey": {
            "aadAuthFailureMode": search.AadAuthFailureMode.HTTP403,
        },
    },
    tags={'createdBy': 'Pulumi'},
    opts=pulumi.ResourceOptions(depends_on=[resource_group])
)

# Storage Account
storage_account = storage.StorageAccount(str(prefix.lower()) + "aidata",
    account_name=str(prefix.lower()) + "aidata",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind='StorageV2',
    tags={
        'createdby': 'Pulumi',
        'ProjectType': 'aoai-your-data-service',
    },
    allow_blob_public_access=False,
    allow_cross_tenant_replication=False,
    allow_shared_key_access=True,
    minimum_tls_version='TLS1_2',
    network_rule_set=storage.NetworkRuleSetArgs(
        bypass='AzureServices',
        default_action='Allow',
    ),
    public_network_access='Enabled',
    encryption=storage.EncryptionArgs(
        key_source='Microsoft.Storage',
        services=storage.EncryptionServicesArgs(
            blob=storage.EncryptionServiceArgs(
                enabled=True,
            ),
            file=storage.EncryptionServiceArgs(
                enabled=True,
            ),
        ),
    ),
    access_tier=storage.AccessTier.HOT,
    opts=pulumi.ResourceOptions(depends_on=[resource_group])
)

# Storage Blob Container
blob_container = storage.BlobContainer(str(prefix.lower()) + "wiki",
    account_name=storage_account.name,
    container_name=str(prefix.lower()) + "wiki",
    resource_group_name=resource_group.name,
    public_access=storage.PublicAccess.NONE,
    opts=pulumi.ResourceOptions(depends_on=[storage_account])
)

# CORS Rules for Storage Account
cors_rule = storage.CorsRuleArgs(
    allowed_headers=["*"],
    allowed_methods=["GET", "OPTIONS", "POST", "PUT"],
    allowed_origins=["*"],
    exposed_headers=["*"],
    max_age_in_seconds=200,
)

blob_service_properties = storage.BlobServiceProperties(
    "blobServiceProperties",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    blob_services_name="default",  # Correct resource name
    cors=storage.CorsRulesArgs(
        cors_rules=[cors_rule]
    ),
    delete_retention_policy=storage.DeleteRetentionPolicyArgs(
        days=7,
        enabled=True
    ),
    opts=pulumi.ResourceOptions(depends_on=[storage_account])
)

# Assign roles to the Azure OpenAI resource's managed identity
search_service_contributor_role_assignment = authorization.RoleAssignment(
    "searchServiceContributorRoleAssignment",
    principal_id=cognitive_account.identity.principal_id,
    principal_type="ServicePrincipal",  # Add this line
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/7ca78c08-252a-4471-8644-bb5ff32d4ba0",  # Search Service Contributor role ID
    scope=search_service.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service, cognitive_account]),
)

search_index_data_reader_role_assignment = authorization.RoleAssignment(
    "searchIndexDataReaderRoleAssignment",
    principal_id=cognitive_account.identity.principal_id,
    principal_type="ServicePrincipal",  # Add this line
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/1407120a-92aa-4202-b7e9-c0e197c71c8f",  # Search Index Data Reader role ID
    scope=search_service.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service, cognitive_account]),
)


# Assign roles to the Azure AI Search system-assigned managed identity
cognitive_services_openai_contributor_role_assignment = authorization.RoleAssignment(
    "cognitiveServicesOpenaiContributorRoleAssignment",
    principal_id=search_service.identity.principal_id,
    principal_type="ServicePrincipal",  # Add this line
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/a001fd3d-188f-4b5d-821b-7da978bf7442",  # Cognitive Services OpenAI Contributor role ID
    scope=cognitive_account.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service, cognitive_account]),
)

storage_blob_data_contributor_role_assignment_search = authorization.RoleAssignment(
    "storageBlobDataContributorRoleAssignmentSearch",
    principal_id=search_service.identity.principal_id,
    principal_type="ServicePrincipal",  # Add this line
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",  # Storage Blob Data Contributor role ID
    scope=storage_account.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service, storage_account]),
)

# Assign roles to the Azure OpenAI managed identity for the Storage account
storage_blob_data_contributor_role_assignment_openai = authorization.RoleAssignment(
    "storageBlobDataContributorRoleAssignmentOpenai",
    principal_id=cognitive_account.identity.principal_id,
    principal_type="ServicePrincipal",  # Add this line
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",  # Storage Blob Data Contributor role ID
    scope=storage_account.id,
    opts=pulumi.ResourceOptions(depends_on=[cognitive_account, storage_account]),
)

##### Migrated the Automation Account to EIP-TASKS #####
"""
# Create an Azure Automation Account
automation_account = automation.AutomationAccount(
    str(prefix.lower()) + "-ai-search-update",
    automation_account_name=str(prefix.lower()) + "-ai-search-update",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=automation.SkuArgs(name='Basic'),
    identity=automation.IdentityArgs(
        type='SystemAssigned'
    ),
    opts=pulumi.ResourceOptions(depends_on=[resource_group]),
    tags={'createdBy': 'Pulumi'}
)

# Define variables and their encryption settings
variables = [
    {"name": "aiUpdate-gitToken", "is_encrypted": True},
    {"name": "aiUpdate-gitRepo", "is_encrypted": False},
    {"name": "aiUpdate-gitFolderPath", "is_encrypted": False},
    {"name": "aiUpdate-fileAgeDays", "is_encrypted": False},
    {"name": "aiUpdate-azBlobConnectStr", "is_encrypted": True},
    {"name": "aiUpdate-azBlobContainer", "is_encrypted": False},
    {"name": "aiUpdate-searchSvcEp", "is_encrypted": False},
    {"name": "aiUpdate-searchSvcKey", "is_encrypted": True},
]

# Create variables for the Automation Account
for variable in variables:
    automation.Variable(
        resource_name=f"{variable['name']}-variable",  # Unique Pulumi resource name
        resource_group_name=resource_group.name,
        automation_account_name=automation_account.name,
        name=variable["name"],  # Correct property for the Azure Automation Variable name
        is_encrypted=variable["is_encrypted"],
        value="",  # Blank value; users can update this in the portal
        opts=pulumi.ResourceOptions(depends_on=[automation_account])
    )

# Assign Contributor role to the Automation Account over the resource group
contributor_role_assignment_automation = authorization.RoleAssignment(
    "contributorRoleAssignmentAutomation",
    principal_id=automation_account.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor role ID
    scope=resource_group.id,
    opts=pulumi.ResourceOptions(depends_on=[resource_group, automation_account])
)
"""
###### Attempted to create index but with these managed ID roles but recieved error for not enough permission.  Went with API key instead, keeping this code for reference ######
"""
# Assign Storage Blob Data Reader role to Azure OpenAI managed identity
storage_blob_data_reader_role_assignment_openai = authorization.RoleAssignment(
    "storageBlobDataReaderRoleAssignmentOpenai",
    principal_id=cognitive_account.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",  # Storage Blob Data Reader role ID
    scope=storage_account.id,
    opts=pulumi.ResourceOptions(depends_on=[cognitive_account, storage_account]),
)

# Assign Storage Blob Data Reader role to Azure AI Search managed identity
storage_blob_data_reader_role_assignment_search = authorization.RoleAssignment(
    "storageBlobDataReaderRoleAssignmentSearch",
    principal_id=search_service.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",  # Storage Blob Data Reader role ID
    scope=storage_account.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service, storage_account]),
)

# Assign Search Service Contributor role to Azure OpenAI managed identity
search_service_contributor_role_assignment_openai = authorization.RoleAssignment(
    "searchServiceContributorRoleAssignmentOpenai",
    principal_id=cognitive_account.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",  # Search Service Contributor role ID
    scope=search_service.id,
    opts=pulumi.ResourceOptions(depends_on=[cognitive_account, search_service]),
)

# Assign Search Service Contributor role to Azure AI Search managed identity
search_service_contributor_role_assignment_search = authorization.RoleAssignment(
    "searchServiceContributorRoleAssignmentSearch",
    principal_id=search_service.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",  # Search Service Contributor role ID
    scope=search_service.id,
    opts=pulumi.ResourceOptions(depends_on=[search_service]),
)
"""
# Outputs
pulumi.export('cognitive_account_name', cognitive_account.name)
pulumi.export('gpt_5.1_deployment_name', gpt_5_1_deployment.name)
pulumi.export('search_service_name', search_service.name)
pulumi.export('storage_account_name', storage_account.name)
pulumi.export('blob_container_name', blob_container.name)
#pulumi.export('automation_account_name', automation_account.name)
pulumi.export('log_analytics_workspace_name', log_analytics_workspace.name)