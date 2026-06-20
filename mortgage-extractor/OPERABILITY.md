# Operability Design: Part 2

## 1. Human Review Tool (Label Studio)
We chose **Label Studio** as the open-source human review interface. It is lightweight, supports JSON/PDF side-by-side views, and can be self-hosted locally on an analyst's machine or deployed via Docker on an internal server. 

When our pipeline flags a document with `REQUIRES_REVIEW` (like our `loan_doc.pdf` which had mathematical discrepancies), the `assignment.json` is loaded into Label Studio. The ops analyst sees the original PDF alongside the extracted fields, with the low-confidence or discrepant fields explicitly highlighted. They manually correct the value, verify the math, and click "Submit."

> **[PLACEHOLDER: Insert your screenshot of Label Studio here]**

## 2. CI/CD Plan (Non-Technical View)
When an analyst corrects a number in Label Studio, that correction doesn't instantly change the live code or the main database. Instead, it triggers an automated workflow in **Jenkins**:
1. **Automated Checks:** Jenkins runs a quick script to ensure the analyst's correction actually makes the math balance (checking if the new numbers fix the subtotal error).
2. **Human Approval:** The corrected extraction is sent to **Forgejo** (our internal repository) as a proposed update. A senior analyst or manager reviews it and clicks "Approve."
3. **Production:** Once approved, the verified data flows into the final database, and the corrected example is saved to our training library.

## 3. Definition of "Retraining"
In this architecture, we do not perform expensive, traditional "fine-tuning" of the AI model. Instead, "retraining" means **Prompt Optimization via Few-Shot Learning**. 

When an analyst corrects a mistake, that specific document and its corrected JSON are automatically added to an internal database of "examples." Once a week, our pipeline updates the system prompt to include these new examples. This teaches the AI exactly how to handle that specific edge-case (like a weird county tax format) the next time it sees it, improving accuracy without writing new code or training weights.

## 4. Operator Manual (For the Ops Analyst)
"This tool automatically reads mortgage PDFs and extracts the numbers for you. Most of the time, it does this perfectly. However, if it finds numbers that don't add up, or if it sees a blurry stamp, it will pause and flag the document for you. Your job is to open the document in the review screen, look at the highlighted red fields, type in the correct number from the PDF, and hit Submit. The system will learn from your corrections so it doesn't make the same mistake twice."
