# Automated Queue Runner Setup (Windows Task Scheduler)

This guide walks through configuring the existing queue automation so it can run headlessly on a Windows Server host (such as your AWS VM). Follow the steps in order—each section builds on the previous one.

## 1. Confirm the code is runnable outside the GUI
1. Log on to the VM with an account that has permission to run scheduled tasks.
2. Open **Command Prompt** (or **Windows Terminal**) and navigate to the repository root. For example:
   ```bat
   cd /d C:\Users\Public\Documents\freight-optimizer
   ```
3. Activate the Python environment you use for the manual runs. If you are using a virtual environment, do so before continuing, e.g.:
   ```bat
   C:\Users\Public\Documents\freight-optimizer\.venv\Scripts\activate
   ```
4. Manually execute the queue runner once to confirm it completes successfully:
   ```bat
   python scripts\run_from_queue.py
   ```
   *You should see either "No items in queue" or the script will pull a queued run, push status back to the database, and exit without errors.*

## 2. Review and update the helper batch file
The repository includes `run_from_queue.bat`, which Task Scheduler will call. Ensure it points to the correct working directory and Python interpreter.

1. Open `run_from_queue.bat` in a text editor with administrator rights.
2. Adjust the `cd /d ...` path if the repository lives somewhere other than `C:\Users\Public\Documents\freight-optimizer`.
3. (Optional) Pin the Python interpreter explicitly if you do not rely on the machine-wide `python` command. For example:
   ```bat
   cd /d C:\Users\Public\Documents\freight-optimizer
   "C:\Users\Public\Documents\freight-optimizer\.venv\Scripts\python.exe" scripts\run_from_queue.py
   ```
4. Save the file.

## 3. Prepare credentials and network access
The automation uses database credentials and posts results to the Logic App webhook embedded in `scripts\run_from_queue.py`.

- Confirm that the VM can reach the database server and the Azure Logic App endpoint over the required ports (usually 443 for HTTPS).
- If the database credentials changed during the migration, update them in `configurations/gui_configurations.json` (the queue runner reads the same configuration as the GUI).
- Ensure the Windows account that will run the task can access any required network shares or VPN connections.

## 4. Create the scheduled task
1. Launch **Task Scheduler** (`taskschd.msc`).
2. In the **Actions** pane, choose **Create Task...** (recommended over "Basic Task" for more control).
3. On the **General** tab:
   - Name the task (e.g., "Freight Optimizer Queue Runner").
   - Select **Run whether user is logged on or not**.
   - Check **Run with highest privileges** if database/network access requires elevation.
4. On the **Triggers** tab:
   - Click **New...** and set the schedule (e.g., repeat every 5 minutes indefinitely).
   - Enable **Stop task if it runs longer than** if you want to prevent overlap.
5. On the **Actions** tab:
   - Click **New...**.
   - **Action**: *Start a program*.
   - **Program/script**: `C:\Windows\System32\cmd.exe`
   - **Add arguments (optional)**: `/c "C:\Users\Public\Documents\freight-optimizer\run_from_queue.bat"`
   - **Start in (optional)**: `C:\Users\Public\Documents\freight-optimizer`
6. On the **Conditions** tab:
   - Uncheck **Start the task only if the computer is on AC power** if running on a server without a battery.
   - Disable **Stop if the computer switches to battery power** as appropriate.
7. On the **Settings** tab:
   - Enable **Allow task to be run on demand**.
   - Decide whether to **Run task as soon as possible after a scheduled start is missed**.
8. Click **OK**, provide the service account password when prompted, and finish.

## 5. Test the scheduled task
1. In Task Scheduler, right-click the new task and choose **Run**.
2. Monitor **History** (enable it if necessary) to confirm the action completed successfully.
3. Check the optimizer database queue to ensure items move from pending to completed, and verify downstream systems receive the webhook payload.
4. Review Task Scheduler's **Last Run Result** and `C:\Users\Public\Documents\freight-optimizer\logs` (if you maintain logs) for any errors.

## 6. Operational tips
- If you need to take the automation offline temporarily, disable the task from Task Scheduler instead of deleting it.
- When updating the code, pause the scheduled task, pull the latest changes, test manually, and re-enable the task.
- To avoid overlapping executions, keep the trigger cadence longer than the longest expected optimization run or enable the **Do not start a new instance** setting under **Settings ➜ If the task is already running**.

Following these steps will recreate the original Azure VM automation on your AWS VM using the built-in queue runner script.
