# BacPacman Polishing Plan

This document outlines a detailed plan for adding a layer of professional polish and improving the overall user experience of the `bacpacman` utility.

## Guiding Principles

* **Clarity:** The user should always understand what is happening and what is expected of them.
* **Safety:** The user should feel confident that they won't make a mistake, with clear confirmations before any critical action.
* **Pleasure:** The interface should be visually appealing and feel responsive and modern.
* **Helpfulness:** The tool should provide helpful guidance, especially when things go wrong.

---

## Detailed Polish Tasks

### 1. Rich, Interactive Prompts (Phase 2 Completion)

This is the core of the user experience overhaul we've started.

* **Task:** Fully replace all remaining `click.prompt` calls with `questionary` equivalents.
* **Details:**
  * Use `questionary.select` for all list-based choices (authentication method, subscription, server, database). This provides arrow-key navigation and a clean interface.
  * Use `questionary.text` for manual text entry (server/database names in fallback mode, SQL username).
  * Use `questionary.password` for securely entering the SQL password.
  * Use `questionary.confirm` for the final "Proceed?" step.

### 2. Implement a Consistent and Appealing Color Scheme

Color should be used purposefully to guide the user's attention and convey status at a glance.

* **Task:** Define and use a custom `questionary.Style` for all prompts.
* **Details:**
  * **Primary/Action Color (e.g., Purple `#673ab7`):** For the question mark, pointer, and highlighted items. This draws the eye to the current action.
  * **Success Color (e.g., Green `#00ff00`):** For all messages indicating a successful operation (e.g., "Successfully extracted bacpac...").
  * **Warning Color (e.g., Yellow `#ffff00`):** For non-critical issues or informational messages (e.g., "Could not connect to Azure, falling back to manual entry.").
  * **Error Color (e.g., Red `#ff0000`):** For critical failures (e.g., "'sqlpackage' command failed.").
  * **Instructional Text (e.g., Grey `#858585`):** For hints and instructions within prompts.
  * **Contrast Check:** The chosen colors should be tested for readability on both light and dark terminal backgrounds.

### 3. Provide Clear Progress Indication

Long-running operations should never leave the user staring at a dead cursor.

* **Task:** Add progress indicators for all potentially slow operations.
* **Details:**
  * **Research `questionary` Spinners:** I will investigate the correct way to implement an animated spinner for asynchronous tasks. If `questionary` itself doesn't support this out of the box, I will research a compatible library (like `halo` or `yaspin`) that can be integrated cleanly.
  * **Implementation:** Wrap all network calls (listing subscriptions, servers, databases) and the final `sqlpackage` subprocess call in a spinner to provide immediate visual feedback.

### 4. Enhance User Guidance and Clarity

The tool should be self-explanatory.

* **Task:** Improve the text and structure of the workflow.
* **Details:**
  * **Section Headers:** Use `questionary.print` with a distinct style (e.g., bold, underlined) to introduce each major step of the workflow (e.g., "--- Step 1: Select Subscription ---").
  * **Informational Text:** Add brief, helpful sentences to explain *why* a step is happening. For example, before listing subscriptions: "First, let's choose which Azure subscription to work with."
  * **Confirmation Summary:** The final confirmation prompt should present a clean, well-formatted summary of all the user's choices before they commit to the extraction.

### 5. Add a Clean Welcome Message

A simple, clean welcome message sets a professional tone.

* **Task:** Add a welcome message at the very beginning of the `full_workflow`.
* **Details:**
  * Use `questionary.print` to display a stylized title. For example, a bold, colored line:
        `BacPacman: Azure SQL Database Exporter`
  * This is understated, informative, and avoids unnecessary visual clutter.

### 6. Final Touches

* **Task:** Review all user-facing text for clarity, grammar, and spelling.
* **Task:** Add a "Goodbye" message upon successful completion or graceful exit.

---

This detailed plan will guide the final stage of development, focusing entirely on creating a high-quality, professional, and pleasant user experience.
