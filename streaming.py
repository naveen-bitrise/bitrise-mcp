"""
Streaming functionality for Bitrise build monitoring.
Handles real-time build progress updates using MCP streaming.
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Optional


async def stream_build_progress(app_slug: str, build_slug: str, poll_interval: int, call_api_func, get_build_log_func) -> str:
    """
    Stream real-time build progress updates using MCP streaming.
    
    Args:
        app_slug: Bitrise app identifier
        build_slug: Build identifier  
        poll_interval: Polling interval in seconds
        call_api_func: Function to make Bitrise API calls
        get_build_log_func: Function to fetch build logs
    
    Returns:
        JSON string with final build status and information
    """
    print(f"📡 stream_build_progress called: {app_slug}/{build_slug}, interval={poll_interval}s")
    
    last_status = None
    update_count = 0
    start_time = datetime.now()
    
    # In a real MCP streaming implementation, this would use SSE
    # For now, we'll simulate by polling and returning a comprehensive update
    
    try:
        while True:
            print(f"📡 Polling build status... (elapsed: {datetime.now() - start_time})")
            
            # Get current build status
            build_url = f"https://api.bitrise.io/v0.1/apps/{app_slug}/builds/{build_slug}"
            build_response = await call_api_func("GET", build_url)
            build_data = json.loads(build_response)
            
            current_status = build_data["data"].get("status")
            current_status_text = build_data["data"].get("status_text", "")
            
            print(f"🔍 Status: {current_status}, Last: {last_status}, Text: {current_status_text}", flush=True)
            
            # Check if status changed
            if current_status != last_status:
                last_status = current_status
                update_count += 1
                
                # Build is complete (success, failed, or aborted)
                if current_status in [1, 2, 3]:  # 1=success, 2=failed, 3=aborted
                    status_name = {1: "SUCCESS", 2: "FAILED", 3: "ABORTED"}.get(current_status, "UNKNOWN")
                    
                    # Get final logs for completed builds
                    final_info = f"Build {status_name.lower()}"
                    
                    try:
                        if current_status == 2:  # Failed - get first failed step
                            log_response = await get_build_log_func(app_slug, build_slug, compact_logs=1)
                            final_info += f"\n\nBuild logs (first failed step):\n{log_response}"
                        elif current_status == 1:  # Success - get build summary
                            log_response = await get_build_log_func(app_slug, build_slug, compact_logs=0)
                            final_info += f"\n\nBuild summary:\n{log_response}"
                        else:  # Aborted - no logs needed
                            final_info += f"\n\nBuild was aborted"
                    except Exception as e:
                        final_info += f"\nCould not fetch build logs: {e}"
                    
                    elapsed = datetime.now() - start_time
                    return json.dumps({
                        "status": "completed",
                        "build_status": status_name,
                        "status_text": current_status_text,
                        "elapsed_time": str(elapsed),
                        "updates_sent": update_count,
                        "final_info": final_info
                    }, indent=2)
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            
            # Safety timeout (2 minutes for testing)
            if (datetime.now() - start_time).total_seconds() > 120:
                return json.dumps({
                    "status": "timeout",
                    "message": "Build monitoring timed out after 10 minutes",
                    "last_status": current_status,
                    "elapsed_time": str(datetime.now() - start_time)
                }, indent=2)
                
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error monitoring build: {str(e)}",
            "elapsed_time": str(datetime.now() - start_time)
        }, indent=2)


async def stream_build_progress_with_notifications(
    app_slug: str, 
    build_slug: str, 
    poll_interval: int,
    ctx,  # MCP Context
    call_api_func,
    get_build_log_func
) -> str:
    """
    Stream build progress using MCP progress notifications.
    
    Args:
        app_slug: Bitrise app identifier
        build_slug: Build identifier  
        poll_interval: Polling interval in seconds
        ctx: MCP context for progress notifications
        call_api_func: Function to make Bitrise API calls
        get_build_log_func: Function to fetch build logs
    
    Returns:
        JSON string with final build status and information
    """
    print(f"📡 MCP streaming started: {app_slug}/{build_slug}, interval={poll_interval}s")
    
    last_status = None
    start_time = datetime.now()
    
    # Send initial progress notification
    await ctx.report_progress(
        progress=0.1,
        total=1.0,
    )
    
    # Start background monitoring task (don't await it)
    import asyncio
    asyncio.create_task(monitor_build_progress(app_slug, build_slug, poll_interval, ctx, call_api_func, get_build_log_func))
    
    # Return immediately after background task is created - no return value needed


async def monitor_build_progress(app_slug: str, build_slug: str, poll_interval: int, ctx, call_api_func, get_build_log_func):
    """Background task to monitor build progress."""
    last_status = None
    start_time = datetime.now()
    
    try:
        while True:
            print(f"📡 Polling build status... (elapsed: {datetime.now() - start_time})")
            
            # Get current build status
            build_url = f"https://api.bitrise.io/v0.1/apps/{app_slug}/builds/{build_slug}"
            build_response = await call_api_func("GET", build_url)
            build_data = json.loads(build_response)
            
            current_status = build_data["data"].get("status")
            current_status_text = build_data["data"].get("status_text", "")
            build_number = build_data["data"].get("build_number", "N/A")
            
            # Calculate elapsed time
            elapsed = datetime.now() - start_time
            elapsed_str = f"{int(elapsed.total_seconds()//60)}:{int(elapsed.total_seconds()%60):02d}"
            
            # Send progress update with status info
            progress_value = 0.5 if current_status == 0 else 0.9  # 0=in-progress, others=near completion
            
            await ctx.report_progress(
                progress=progress_value,
                total=1.0,
            )
            
            # Check if status changed
            if current_status != last_status:
                status_name = {0: "IN-PROGRESS", 1: "SUCCESS", 2: "FAILED", 3: "ABORTED"}.get(current_status, "UNKNOWN")
                
                # Log progress message
                await ctx.info(f"Build #{build_number} {status_name}: {current_status_text} (elapsed: {elapsed_str})")
                
                last_status = current_status
                
                # Build is complete (success, failed, or aborted)
                if current_status in [1, 2, 3]:  # 1=success, 2=failed, 3=aborted
                    # Send final progress notification
                    await ctx.report_progress(
                        progress=1.0,
                        total=1.0,
                    )
                    
                    # Send appropriate completion message
                    if current_status == 1:  # Success
                        await ctx.info(f"Build #{build_number} succeeded after {elapsed_str}")
                    elif current_status == 2:  # Failed
                        await ctx.info(f"Build #{build_number} failed after {elapsed_str}. Ask Agent to get build logs for Build#{build_number} to see the issue")
                    else:  # Aborted
                        await ctx.info(f"Build #{build_number} was aborted after {elapsed_str}")
                    
                    # Check if this build has a temporary branch that needs cleanup
                    await cleanup_temp_branch_if_tracked(build_slug, ctx)
                    
                    return  # End background monitoring
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            
            # Safety timeout (10 minutes)
            if elapsed.total_seconds() > 600:
                await ctx.report_progress(progress=1.0, total=1.0)
                await ctx.info("Build monitoring timed out after 10 minutes")
                return
                
    except Exception as e:
        await ctx.report_progress(progress=1.0, total=1.0)
        await ctx.info(f"Error monitoring build: {str(e)}")
        return



async def push_temp_branch(repo_path: str, commit_message: Optional[str], ctx) -> str:
    """
    Push local changes to temporary remote branch without affecting local state.
    Returns the branch name.
    """
    temp_branch = f"temp-build-{int(datetime.now().timestamp())}"
    
    if commit_message is None:
        commit_message = f"Temporary build validation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Check if path is a git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise Exception(f"Not a git repository: {repo_path}")
    
    # Check if remote 'origin' exists
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise Exception(f"Remote 'origin' issue in {repo_path}: {error_msg}")
        
        remote_url = result.stdout.strip()
        if not remote_url:
            raise Exception(f"Remote 'origin' exists but has no URL configured in {repo_path}")
            
        await ctx.info(f"📡 Remote origin found: {remote_url}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Git command failed in {repo_path}: {e}")
    
    await ctx.info(f"🔧 Creating temporary branch '{temp_branch}' with your changes...")
    
    try:
        # Save current state before making any changes
        try:
            original_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            await ctx.info("⚠️ Could not check git status, proceeding anyway...")
            original_status = None
        
        staged_files = False
        remote_pushed = False
        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
            staged_files = True
            
            # Create tree from index
            tree_sha = subprocess.run(
                ["git", "write-tree"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # Get HEAD commit
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # Create commit object
            commit_sha = subprocess.run(
                ["git", "commit-tree", tree_sha, "-p", head_sha, "-m", commit_message],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # Reset index to restore local state (CRITICAL - always do this)
            # Use --mixed to unstage files but keep working directory changes
            subprocess.run(["git", "reset", "--mixed", "HEAD"], cwd=repo_path, check=True)
            staged_files = False  # Successfully reset
            
            await ctx.info(f"📤 Pushing temporary branch to remote...")
            
            # Push to remote
            subprocess.run(
                ["git", "push", "origin", f"{commit_sha}:refs/heads/{temp_branch}"],
                cwd=repo_path,
                check=True
            )
            remote_pushed = True  # Track that remote push succeeded
            
            await ctx.info(f"✅ Temporary branch '{temp_branch}' pushed successfully")
            return temp_branch
            
        except subprocess.CalledProcessError as e:
            # Critical: Clean up both local and remote state if needed
            
            # 1. Clean up staged files if needed
            if staged_files:
                try:
                    await ctx.info("🔧 Cleaning up staged files...")
                    subprocess.run(["git", "reset", "--mixed", "HEAD"], cwd=repo_path, check=True)
                    await ctx.info("✅ Staged files cleaned up successfully")
                except subprocess.CalledProcessError as reset_error:
                    await ctx.info(f"❌ CRITICAL: Failed to reset staged files! Manual cleanup may be needed: {reset_error}")
                    # Continue to try remote cleanup even if local cleanup failed
            
            # 2. Clean up remote branch if it was pushed
            if remote_pushed:
                try:
                    await ctx.info(f"🔧 Cleaning up remote branch '{temp_branch}'...")
                    subprocess.run(["git", "push", "origin", "--delete", temp_branch], cwd=repo_path, check=True)
                    await ctx.info(f"✅ Remote branch '{temp_branch}' cleaned up successfully")
                except subprocess.CalledProcessError as cleanup_error:
                    await ctx.info(f"⚠️ Failed to delete remote branch '{temp_branch}': {cleanup_error}")
                    await ctx.info(f"⚠️ Manual cleanup needed: git push origin --delete {temp_branch}")
            
            await ctx.info(f"❌ Git operation failed: {e}")
            
            # If both local and remote cleanup had issues, provide comprehensive error
            if staged_files and remote_pushed:
                raise Exception(f"Git operation failed. Repository may need manual cleanup of both local staged files and remote branch '{temp_branch}': {e}")
            elif staged_files:
                raise Exception(f"Git operation failed AND failed to reset staged files. Repository may be in inconsistent state: {e}")
            elif remote_pushed:
                raise Exception(f"Git operation failed. Remote branch '{temp_branch}' may need manual deletion: {e}")
            else:
                raise Exception(f"Git operation failed: {e}")
        
    except Exception as e:
        await ctx.info(f"❌ Unexpected error during git operations: {e}")
        raise


async def cleanup_temp_branch(branch_name: str, repo_path: str, ctx) -> bool:
    """
    Clean up a temporary branch from remote repository.
    Returns True if successful, False otherwise.
    """
    try:
        await ctx.info(f"🗑️ Cleaning up temporary branch '{branch_name}'...")
        
        subprocess.run(
            ["git", "push", "origin", "--delete", branch_name],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        
        await ctx.info(f"✅ Temporary branch '{branch_name}' deleted successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        await ctx.info(f"⚠️ Failed to delete temporary branch '{branch_name}': {e}")
        return False


async def cleanup_temp_branch_if_tracked(build_slug: str, ctx):
    """
    Clean up temporary branch if this build was started from validate_update_fix.
    """
    try:
        # Import here to avoid circular dependencies
        from main import TEMP_BRANCH_TRACKER
        
        if build_slug in TEMP_BRANCH_TRACKER:
            branch_info = TEMP_BRANCH_TRACKER[build_slug]
            
            if not branch_info.get("cleanup_attempted", False):
                branch_name = branch_info["branch_name"]
                repo_path = branch_info["repo_path"]
                
                await ctx.info(f"🗑️ Cleaning up temporary branch '{branch_name}' for completed build...")
                
                # Mark as attempted to prevent double cleanup
                TEMP_BRANCH_TRACKER[build_slug]["cleanup_attempted"] = True
                
                try:
                    subprocess.run(
                        ["git", "push", "origin", "--delete", branch_name],
                        cwd=repo_path,
                        check=True,
                        capture_output=True
                    )
                    
                    await ctx.info(f"✅ Temporary branch '{branch_name}' deleted successfully")
                    
                    # Remove from tracking since cleanup is complete
                    del TEMP_BRANCH_TRACKER[build_slug]
                    
                except subprocess.CalledProcessError as e:
                    await ctx.info(f"⚠️ Failed to delete temporary branch '{branch_name}': {e}")
                    # Keep in tracker for potential manual cleanup
                    
    except ImportError:
        # TEMP_BRANCH_TRACKER not available, skip cleanup
        pass
    except Exception as e:
        await ctx.info(f"⚠️ Error during temp branch cleanup: {e}")


def get_build_status_description(status_code: Optional[int]) -> str:
    """Get human-readable build status description."""
    status_map = {
        0: "not finished yet",
        1: "successful",
        2: "failed", 
        3: "aborted",
        4: "in-progress"
    }
    return status_map.get(status_code, "unknown")


# FOR TESTING - Copy of trigger_bitrise_build function
async def test_trigger_bitrise_build(
    app_slug: str,
    branch: str = "main",
    workflow_id: str = None,
    pipeline_id: str = None,
    commit_message: str = None,
    commit_hash: str = None,
    rebuild_build_slug: str = None,
    stream_progress: bool = False,
    poll_interval: int = 30,
    call_api_func = None,
    get_build_log_func = None
) -> str:
    """Testing version of trigger_bitrise_build function."""
    import httpx
    
    # Default API call function
    if not call_api_func:
        async def default_call_api(method: str, url: str, body=None):
            print(f"🌐 API call: {method} {url}", flush=True)
            import sys; sys.stdout.flush()
            try:
                headers = {
                    'Authorization': os.environ.get("BITRISE_TOKEN", ""),
                    'Content-Type': 'application/json',
                }
                async with httpx.AsyncClient() as client:
                    print(f"📤 Making {method} request...", flush=True)
                    if method == "GET":
                        response = await client.get(url, headers=headers, timeout=30.0)
                    elif method == "POST":
                        response = await client.post(url, headers=headers, json=body, timeout=30.0)
                    print(f"📥 Response received: {response.status_code}", flush=True)
                    response.raise_for_status()
                    print(f"✅ Response OK, length: {len(response.text)}", flush=True)
                    print(f"🔍 Response preview: {response.text[:200]}...", flush=True)
                    return response.text
            except Exception as e:
                print(f"❌ API call failed: {e}")
                raise
        call_api_func = default_call_api
    
    url = f"https://api.bitrise.io/v0.1/apps/{app_slug}/builds"
    
    # Handle rebuild logic
    if rebuild_build_slug:
        # Fetch original build parameters
        original_build_url = f"https://api.bitrise.io/v0.1/apps/{app_slug}/builds/{rebuild_build_slug}"
        original_build_response = await call_api_func("GET", original_build_url)
        
        try:
            original_build_response_data = json.loads(original_build_response)
            original_build_data = original_build_response_data.get("data", {})
            original_params = original_build_data.get("original_build_params", {})
            
            # Debug output
            print(f"🔧 DEBUG: Original build data keys: {list(original_build_data.keys())}")
            print(f"🔧 DEBUG: Original params: {original_params}")
            
            # Use original parameters, but allow overrides from function parameters
            build_params = {
                "branch": branch if branch != "main" else original_params.get("branch", "main"),
            }
            
            # Use original workflow/pipeline if not overridden
            if not workflow_id and not pipeline_id:
                if original_params.get("workflow_id"):
                    build_params["workflow_id"] = original_params["workflow_id"]
                elif original_params.get("pipeline_id"):
                    build_params["pipeline_id"] = original_params["pipeline_id"]
            
            # Use function parameters if provided, otherwise use original
            if pipeline_id:
                build_params["pipeline_id"] = pipeline_id
            if workflow_id:
                build_params["workflow_id"] = workflow_id
            if commit_message:
                build_params["commit_message"] = commit_message
            elif original_params.get("commit_message"):
                build_params["commit_message"] = original_params["commit_message"]
            if commit_hash:
                build_params["commit_hash"] = commit_hash
            elif original_params.get("commit_hash"):
                build_params["commit_hash"] = original_params["commit_hash"]
                
        except (json.JSONDecodeError, KeyError) as e:
            return f"Failed to parse original build data for rebuild: {e}"
    else:
        # Normal build parameters
        build_params = {"branch": branch}

        if pipeline_id:
            build_params["pipeline_id"] = pipeline_id
        if workflow_id:
            build_params["workflow_id"] = workflow_id
        if commit_message:
            build_params["commit_message"] = commit_message
        if commit_hash:
            build_params["commit_hash"] = commit_hash

    body = {
        "build_params": build_params,
        "hook_info": {"type": "bitrise"},
    }

    # Debug output
    print(f"🔧 DEBUG: Build parameters: {build_params}")
    print(f"🔧 DEBUG: Request body: {body}")

    # Trigger the build
    print("🔥 About to trigger build...")
    build_response = await call_api_func("POST", url, body)
    print(f"✅ Build triggered! Response length: {len(build_response)}")
    
    # If streaming is not requested, return the trigger response
    if not stream_progress:
        return build_response
    
    # Extract build_slug from response for monitoring
    try:
        build_data = json.loads(build_response)
        build_slug = build_data.get("build_slug")
        if not build_slug:
            return f"Build triggered but could not extract build_slug for monitoring: {build_response}"
    except json.JSONDecodeError:
        return f"Build triggered but could not parse response for monitoring: {build_response}"
    
    # Start streaming build progress
    print(f"🚀 Starting streaming for build: {build_slug}")
    return await stream_build_progress(app_slug, build_slug, poll_interval, call_api_func, get_build_log_func)