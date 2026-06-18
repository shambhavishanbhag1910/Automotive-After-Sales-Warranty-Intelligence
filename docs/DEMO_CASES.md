# Demo Cases - Agentic Automotive Warranty Intelligence

This project demonstrates an AI-driven automotive after-sales warranty workflow using synthetic warranty, dealer, supplier, vehicle, fault-code, and service-history data.

## Case 1: Normal Warranty Processing

**Claim ID:** C0001  
**Scenario:** Valid claim with known VIN, known dealer, known part, and available warranty rule context.  
**Expected Outcome:** Approve for normal warranty processing after analyst confirmation.

## Case 2: Repeat Repair Risk

**Claim ID:** C0002  
**Scenario:** Claim shows possible repeat repair pattern based on VIN/service history.  
**Expected Outcome:** Route to human review for repeat repair investigation.

## Case 3: Supplier Recovery Opportunity

**Claim ID:** C0016  
**Scenario:** Claim is linked to supplier context and fault-code evidence.  
**Expected Outcome:** Recommend supplier recovery packet preparation.

## Case 4: Warranty Eligibility Risk

**Claim ID:** C0003  
**Scenario:** Warranty month, mileage, or policy condition requires validation.  
**Expected Outcome:** Flag eligibility risk and request analyst review.

## Case 5: Weak Evidence / Unknown Fault Context

**Claim ID:** C0004  
**Scenario:** Claim has incomplete evidence, weak diagnostic information, or unknown fault context.  
**Expected Outcome:** Avoid automatic approval and keep under human review.

## Case 6: High-Severity Claim

**Claim ID:** C0005  
**Scenario:** Claim has high severity, high cost, or potential campaign/recall relevance.  
**Expected Outcome:** Escalate for detailed evidence review.