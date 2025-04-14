# Bitrise MCP Server

MCP Server for the Bitrise API, enabling app management, build operations, artifact management and more.

### Features

- **Comprehensive API Access**: Access to Bitrise APIs including apps, builds, artifacts, and more.
- **Authentication Support**: Secure API token-based access to Bitrise resources.
- **Detailed Documentation**: Well-documented tools with parameter descriptions.

## Setup

### Environment Setup
- Python 3.12.6 required (you can use [pyenv](https://github.com/pyenv/pyenv)).
- Use [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management.

#### Example setting up the environment
> Please read the official documentation for uv and pylint for more options.
```bash
# Install pyenv and python 3.12.6
curl -fsSL https://pyenv.run | bash
pyenv install 3.12.6

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Bitrise API Token
[Create a Bitrise API Token](https://devcenter.bitrise.io/api/authentication):
   - Go to your [Bitrise Account Settings/Security](https://app.bitrise.io/me/account/security).
   - Navigate to the "Personal access tokens" section.
   - Copy the generated token.

### Use with [Claude Desktop](https://claude.ai/download)

_This guide uses Claude Desktop as the MCP client, but you can use any other MCP-compatible client and adapt the following config options to your preferred client._

Open Claude settings, then navigate to the Developer tab.

Click _Edit config_. This creates a config file called `claude_desktop_config.json`. Open this file with your preferred editor and add the Bitrise MCP server:

```json
{
  "mcpServers": {
    "bitrise": {
      "command": "uvx",
      "env": {
        "BITRISE_TOKEN": "<YOUR_TOKEN>"
      },
      "args": [
        "--from",
        "git+https://github.com/bitrise-io/bitrise-mcp@v1.0.1",
        "bitrise-mcp"
      ]
    }
  }
}
```

Save the config file and restart Claude Desktop. If everything is set up correctly, you should see a hammer icon next to the message composer.

### Use with [VS Code](https://code.visualstudio.com/Download)

Follow the [official guide](https://code.visualstudio.com/blogs/2025/04/07/agentMode) to enable Agent mode in Copilot Chat.

Then, open VSCode's `settings.json`, and add the Bitrise MCP server configuration under the `mcp.servers` key:

```json
{
  "mcp": {
      "servers": {
          "bitrise": {
              "command": "uvx",
              "args": [
                  "--from",
                  "git+https://github.com/bitrise-io/bitrise-mcp@v1.0.1",
                  "bitrise-mcp"
              ],
              "type": "stdio",
              "env": {
                  "BITRISE_TOKEN": "<YOUR_TOKEN>"
              },
          },
      }
  }
}
```

Save the configuration. VS Code will automatically recognize the change and load the tools into Copilot Chat.

### Advanced configuration

You can limit the number of tools exposed to the MCP client. This is useful if you want to optimize token usage or your MCP client has a limit on the number of tools.

Tools are grouped by their "API group", and you can pass the groups you want to expose as tools. Possible values: `apps, builds, workspaces, webhooks, build-artifacts, group-roles, cache-items, pipelines, account, read-only`.

Example configuration:
```json
{
  "mcpServers": {
    "bitrise": {
      "command": "uvx",
      "env": {
        "BITRISE_TOKEN": "<YOUR_PAT>"
      },
      "args": [
        "--from",
        "git+https://github.com/bitrise-io/bitrise-mcp@v1.0.1",
        "bitrise-mcp",
        "--enabled-api-groups",
        "cache-items,pipelines"
      ]
    }
  }
}
```

## Tools

### Apps

1. `list_apps`
   - List all the apps available for the authenticated account
   - Arguments:
     - `sort_by` (optional): Order of the apps: last_build_at (default) or created_at
     - `next` (optional): Slug of the first app in the response
     - `limit` (optional): Max number of elements per page (default: 50)

2. `register_app`
   - Add a new app to Bitrise
   - Arguments:
     - `repo_url`: Repository URL
     - `is_public`: Whether the app's builds visibility is "public"
     - `organization_slug`: The organization (aka workspace) the app to add to
     - `project_type` (optional): Type of project (ios, android, etc.)
     - `provider` (optional): github

3. `finish_bitrise_app`
   - Finish the setup of a Bitrise app
   - Arguments:
     - `app_slug`: The slug of the Bitrise app to finish setup for
     - `project_type` (optional): The type of project (e.g., android, ios, flutter, etc.)
     - `stack_id` (optional): The stack ID to use for the app
     - `mode` (optional): The mode of setup
     - `config` (optional): The configuration to use for the app

4. `get_app`
   - Get the details of a specific app
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app

5. `delete_app`
   - Delete an app from Bitrise
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app

6. `update_app`
   - Update an app
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app
     - `is_public`: Whether the app's builds visibility is "public"
     - `project_type`: Type of project
     - `provider`: Repository provider
     - `repo_url`: Repository URL

7. `get_bitrise_yml`
   - Get the current Bitrise YML config file of a specified Bitrise app
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app

8. `update_bitrise_yml`
   - Update the Bitrise YML config file of a specified Bitrise app
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app
     - `bitrise_yml_as_json`: The new Bitrise YML config file content

9. `list_branches`
   - List the branches with existing builds of an app's repository
   - Arguments:
     - `app_slug`: Identifier of the Bitrise app

10. `register_ssh_key`
    - Add an SSH-key to a specific app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `auth_ssh_private_key`: Private SSH key
      - `auth_ssh_public_key`: Public SSH key
      - `is_register_key_into_provider_service`: Register the key in the provider service

11. `register_webhook`
    - Register an incoming webhook for a specific application
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

### Builds

12. `list_builds`
    - List all the builds of a specified Bitrise app or all accessible builds
    - Arguments:
      - `app_slug` (optional): Identifier of the Bitrise app
      - `sort_by` (optional): Order of builds: created_at (default), running_first
      - `branch` (optional): Filter builds by branch
      - `workflow` (optional): Filter builds by workflow
      - `status` (optional): Filter builds by status (0: not finished, 1: successful, 2: failed, 3: aborted, 4: in-progress)
      - `next` (optional): Slug of the first build in the response
      - `limit` (optional): Max number of elements per page (default: 50)

13. `trigger_bitrise_build`
    - Trigger a new build/pipeline for a specified Bitrise app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `branch` (optional): The branch to build (default: main)
      - `workflow_id` (optional): The workflow to build
      - `commit_message` (optional): The commit message for the build
      - `commit_hash` (optional): The commit hash for the build

14. `get_build`
    - Get a specific build of a given app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build

15. `abort_build`
    - Abort a specific build
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build
      - `reason` (optional): Reason for aborting the build

16. `get_build_log`
    - Get the build log of a specified build of a Bitrise app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the Bitrise build

17. `get_build_bitrise_yml`
    - Get the bitrise.yml of a build
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build

18. `list_build_workflows`
    - List the workflows of an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

### Build Artifacts

19. `list_artifacts`
    - Get a list of all build artifacts
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build
      - `next` (optional): Slug of the first artifact in the response
      - `limit` (optional): Max number of elements per page (default: 50)

20. `get_artifact`
    - Get a specific build artifact
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build
      - `artifact_slug`: Identifier of the artifact

21. `delete_artifact`
    - Delete a build artifact
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build
      - `artifact_slug`: Identifier of the artifact

22. `update_artifact`
    - Update a build artifact
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `build_slug`: Identifier of the build
      - `artifact_slug`: Identifier of the artifact
      - `is_public_page_enabled`: Enable public page for the artifact

### Webhooks

23. `list_outgoing_webhooks`
    - List the outgoing webhooks of an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

24. `delete_outgoing_webhook`
    - Delete the outgoing webhook of an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `webhook_slug`: Identifier of the webhook

25. `update_outgoing_webhook`
    - Update an outgoing webhook for an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `webhook_slug`: Identifier of the webhook
      - `events`: List of events to trigger the webhook
      - `url`: URL of the webhook
      - `headers` (optional): Headers to be sent with the webhook

26. `create_outgoing_webhook`
    - Create an outgoing webhook for an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `events`: List of events to trigger the webhook
      - `url`: URL of the webhook
      - `headers` (optional): Headers to be sent with the webhook

### Cache Items

27. `list_cache_items`
    - List the key-value cache items belonging to an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

28. `delete_all_cache_items`
    - Delete all key-value cache items belonging to an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

29. `delete_cache_item`
    - Delete a key-value cache item
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `cache_item_id`: Identifier of the cache item

30. `get_cache_item_download_url`
    - Get the download URL of a key-value cache item
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `cache_item_id`: Identifier of the cache item

### Pipelines

31. `list_pipelines`
    - List all pipelines and standalone builds of an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app

32. `get_pipeline`
    - Get a pipeline of a given app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `pipeline_id`: Identifier of the pipeline

33. `abort_pipeline`
    - Abort a pipeline
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `pipeline_id`: Identifier of the pipeline
      - `reason` (optional): Reason for aborting the pipeline

34. `rebuild_pipeline`
    - Rebuild a pipeline
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `pipeline_id`: Identifier of the pipeline

### Group Roles

35. `list_group_roles`
    - List group roles for an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `role_name`: Name of the role

36. `replace_group_roles`
    - Replace group roles for an app
    - Arguments:
      - `app_slug`: Identifier of the Bitrise app
      - `role_name`: Name of the role
      - `group_slugs`: List of group slugs

### Workspaces

37. `list_workspaces`
    - List the workspaces the user has access to

38. `get_workspace`
    - Get details for one workspace
    - Arguments:
      - `workspace_slug`: Slug of the Bitrise workspace

39. `get_workspace_groups`
    - Get the groups in a workspace
    - Arguments:
      - `workspace_slug`: Slug of the Bitrise workspace

40. `create_workspace_group`
    - Create a group in a workspace
    - Arguments:
      - `workspace_slug`: Slug of the Bitrise workspace
      - `group_name`: Name of the group

41. `get_workspace_members`
    - Get the members in a workspace
    - Arguments:
      - `workspace_slug`: Slug of the Bitrise workspace

42. `invite_member_to_workspace`
    - Invite a member to a workspace
    - Arguments:
      - `workspace_slug`: Slug of the Bitrise workspace
      - `email`: Email address of the user

43. `add_member_to_group`
    - Add a member to a group
    - Arguments:
      - `group_slug`: Slug of the group
      - `user_slug`: Slug of the user

### Account

44. `me`
    - Get info from the currently authenticated user account

## API Groups

The Bitrise MCP server organizes tools into API groups that can be enabled or disabled via command-line arguments. The table below shows which API groups each tool belongs to:

| Tool | apps | builds | workspaces | webhooks | build-artifacts | group-roles | cache-items | pipelines | account | read-only |
|------|------|--------|------------|----------|----------------|-------------|-------------|-----------|---------|-----------|
| list_apps | ✅ | | | | | | | | | ✅ |
| register_app | ✅ | | | | | | | | | |
| finish_bitrise_app | ✅ | | | | | | | | | |
| get_app | ✅ | | | | | | | | | ✅ |
| delete_app | ✅ | | | | | | | | | |
| update_app | ✅ | | | | | | | | | |
| get_bitrise_yml | ✅ | | | | | | | | | ✅ |
| update_bitrise_yml | ✅ | | | | | | | | | |
| list_branches | ✅ | | | | | | | | | ✅ |
| register_ssh_key | ✅ | | | | | | | | | |
| register_webhook | ✅ | | | | | | | | | |
| list_builds | | ✅ | | | | | | | | ✅ |
| trigger_bitrise_build | | ✅ | | | | | | | | |
| get_build | | ✅ | | | | | | | | ✅ |
| abort_build | | ✅ | | | | | | | | |
| get_build_log | | ✅ | | | | | | | | ✅ |
| get_build_bitrise_yml | | ✅ | | | | | | | | ✅ |
| list_build_workflows | | ✅ | | | | | | | | ✅ |
| list_artifacts | | | | | ✅ | | | | | ✅ |
| get_artifact | | | | | ✅ | | | | | ✅ |
| delete_artifact | | | | | ✅ | | | | | |
| update_artifact | | | | | ✅ | | | | | |
| list_outgoing_webhooks | | | | ✅ | | | | | | ✅ |
| delete_outgoing_webhook | | | | ✅ | | | | | | |
| update_outgoing_webhook | | | | ✅ | | | | | | |
| create_outgoing_webhook | | | | ✅ | | | | | | |
| list_cache_items | | | | | | | ✅ | | | ✅ |
| delete_all_cache_items | | | | | | | ✅ | | | |
| delete_cache_item | | | | | | | ✅ | | | |
| get_cache_item_download_url | | | | | | | ✅ | | | ✅ |
| list_pipelines | | | | | | | | ✅ | | ✅ |
| get_pipeline | | | | | | | | ✅ | | ✅ |
| abort_pipeline | | | | | | | | ✅ | | |
| rebuild_pipeline | | | | | | | | ✅ | | |
| list_group_roles | | | | | | ✅ | | | | ✅ |
| replace_group_roles | | | | | | ✅ | | | | |
| list_workspaces | | | ✅ | | | | | | | ✅ |
| get_workspace | | | ✅ | | | | | | | ✅ |
| get_workspace_groups | | | ✅ | | | | | | | ✅ |
| create_workspace_group | | | ✅ | | | | | | | |
| get_workspace_members | | | ✅ | | | | | | | ✅ |
| invite_member_to_workspace | | | ✅ | | | | | | | |
| add_member_to_group | | | ✅ | | | | | | | |
| me | | | | | | | | | ✅ | ✅ |

By default, all API groups are enabled. You can specify which groups to enable using the `--enabled-api-groups` command-line argument with a comma-separated list of group names.
