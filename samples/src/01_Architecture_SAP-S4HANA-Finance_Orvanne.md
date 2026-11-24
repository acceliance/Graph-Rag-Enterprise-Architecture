---
title: SAP S/4HANA Finance Architecture Document
subtitle: Accounting block of the Orvanne Group information system
---

## Document control

| Item | Value |
|---|---|
| Title | SAP S/4HANA Finance Architecture Document |
| Reference | ORV-ARC-FIN-001 |
| Version | 2.3 |
| Publication date | 12 October 2026 |
| Document type | Technical architecture document |
| Language | English |
| Status | Approved |
| Confidentiality | Internal, restricted to Orvanne Group and its integration partners |
| Issuer | Orvanne Group IT (the IT department of Orvanne Group) |
| Author | Claire Montfort, Finance Solution Architect, Orvanne Group IT (claire.montfort@orvanne.example) |
| Reviewer | Nadia Benali, Enterprise Architect, Orvanne Group IT (nadia.benali@orvanne.example) |
| Approvers | Hugo Lemaire, Group Chief Information Officer, Orvanne Group IT; Isabelle Roche, Group Chief Financial Officer, Finance Department |

### Revision history

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 14 February 2025 | Claire Montfort | First issue after the go-live of SAP S/4HANA Finance (end of the FINEO S/4HANA Migration project). |
| 2.0 | 9 January 2026 | Claire Montfort | Added the order-to-cash exchanges with the Salesforce Order Platform (O2C-01 to O2C-05) designed by the Horizon O2C project. |
| 2.1 | 20 April 2026 | Claire Montfort | Added Kyriba Treasury and the payment factory exchanges (FIN-03, FIN-04, FIN-05); removed the direct bank connection from SAP. |
| 2.2 | 7 September 2026 | Julien Carpentier | Added the electronic invoicing exchanges with the Esker Invoice Platform (FIN-14, FIN-15) after the go-live of the E-Invoicing 2026 Compliance project. |
| 2.3 | 12 October 2026 | Claire Montfort | Added the Iberia Finance Rollout project and the status of Sage X3 Iberia; added the temporary exchange O2C-08 with OrderDesk; updated infrastructure sizing after the September 2026 capacity review. |

## 1. Purpose and scope

This document describes the architecture of **SAP S/4HANA Finance**, the accounting block of the Orvanne Group information system. It presents the system itself, its satellite applications, the data exchanges between them, the infrastructure it runs on, the technologies it uses, the quality requirements it must meet, the architecture decisions taken, and the projects that change it.

The information system of Orvanne Group is built around two main blocks:

- **SAP S/4HANA Finance**, for accounting. It is the subject of this document.
- **Salesforce Order Platform**, for order management. It is described in the *Salesforce Order Platform Architecture Document* (reference ORV-ARC-O2C-002).

The exchanges between the two blocks (the order-to-cash exchanges, prefixed O2C) are described in both documents, each from the point of view of its own block. Exchanges that involve only the accounting block are prefixed FIN. Exchanges that involve only the order management block are prefixed CRM and are described in ORV-ARC-O2C-002 only.

Out of scope: human resources systems (the Orvanne HR Core is referenced as a source of employee data but is not described in any architecture document yet), manufacturing systems (Orvanne Group subcontracts all manufacturing), and workplace tools.

## 2. Enterprise context

### 2.1 Orvanne Group

Orvanne Group is a business-to-business distributor of commercial heating, ventilation and air-conditioning equipment and spare parts. Its head office is in Lyon, France. In 2025 the group had a revenue of 480 million euros and 2,100 employees. It sells to about 38,000 professional customers (installers, facility managers, building contractors) in France, Germany and Spain.

The group has four legal entities. Each is a company code in SAP S/4HANA Finance, except Orvanne Iberia, which still keeps its books in Sage X3 Iberia.

| Legal entity | Country | SAP company code | Accounting system |
|---|---|---|---|
| Orvanne Group SA (holding) | France | FR01 | SAP S/4HANA Finance |
| Orvanne France SAS | France | FR10 | SAP S/4HANA Finance |
| Orvanne Deutschland GmbH | Germany | DE20 | SAP S/4HANA Finance |
| Orvanne Iberia SL | Spain | ES30 (planned) | Sage X3 Iberia until the Iberia Finance Rollout project is complete |

### 2.2 Organisations involved

| Organisation | Kind | Role for the accounting block |
|---|---|---|
| Orvanne Group | Business (the enterprise) | Owner of the information system |
| Orvanne Group IT | IT department | Operates the on-premise infrastructure, issues architecture documents, runs the integration platforms |
| Finance Department | Business unit of Orvanne Group | Business owner of SAP S/4HANA Finance and of its finance satellites |
| Sales and Customer Operations | Business unit of Orvanne Group | Business owner of the Salesforce Order Platform |
| SAP SE | Vendor | Vendor of SAP S/4HANA, SAP Integration Suite and SAP Concur; operates the RISE with SAP private cloud |
| Microsoft | Hosting provider and vendor | Provides the Azure regions that host SAP S/4HANA Finance and the Orvanne Data Platform; vendor of Microsoft Entra ID |
| Salesforce | Vendor | Vendor of the Salesforce Order Platform and of MuleSoft Anypoint Platform |
| Esker | Vendor | Vendor of the Esker Invoice Platform, an accredited electronic invoicing platform in France |
| Kyriba | Vendor | Vendor of Kyriba Treasury |
| BlackLine | Vendor | Vendor of BlackLine Financial Close |
| ADP | Vendor | Payroll service provider for France and Germany |
| OpenText | Vendor | Vendor of OpenText Archive Center |
| Hardis Group | Vendor | Vendor of Reflex WMS |
| Fortra | Vendor | Vendor of GoAnywhere MFT, the product behind the MFT Gateway |
| Sage | Vendor | Vendor of Sage X3 |
| Cap Solutions Conseil | Vendor (integrator) | Integration partner for SAP S/4HANA Finance since the FINEO S/4HANA Migration project |

### 2.3 Architecture principles

The following principles come from the Orvanne Group architecture charter. They apply to both blocks and are repeated in both architecture documents.

| Principle | Statement |
|---|---|
| One Master per Data Object | Every business data object has exactly one application system that masters it. Other systems receive copies and never change them. |
| No Point-to-Point Integration | Application systems exchange data only through an integration platform (the Orvanne Integration Hub, SAP Integration Suite or the MFT Gateway). Direct connections between two applications are not allowed. |
| Keep the Core Clean | Packaged software is used as delivered. Extensions are built outside the core, on the vendor's extension platform, and no vendor code is modified. |
| SaaS First | A new need is covered first by a software-as-a-service product, then by a private cloud product, and only as a last resort by an on-premise product. |
| Identity Federated Through Entra ID | Every application authenticates its internal users through Microsoft Entra ID with single sign-on. No application stores its own passwords for employees. |
| Data Resides in the European Union | All production data is stored and processed in data centres located in the European Union. |
| Event-Driven Before Batch | A new exchange is designed as an event or an API call. Batch files are accepted only when the partner system cannot do otherwise. |

## 3. Business architecture

SAP S/4HANA Finance and its satellites support the **Finance** business area (code BA-FIN). The table gives each business capability, the application system that supports it, and its maturity on the group's five-level scale (1 initial, 2 repeatable, 3 defined, 4 managed, 5 optimised) as assessed in June 2026, with the target for the end of 2027.

| Code | Business capability | Description | Supported by | Current maturity | Target maturity |
|---|---|---|---|---|---|
| FIN-C01 | General Accounting | Keeps the general ledger, the chart of accounts and the journal entries of every legal entity. | SAP S/4HANA Finance | 4 | 4 |
| FIN-C02 | Accounts Payable | Receives, checks, approves and pays supplier invoices. | Esker Invoice Platform, SAP S/4HANA Finance | 4 | 5 |
| FIN-C03 | Accounts Receivable | Issues customer invoices, records customer payments and follows open items. | SAP S/4HANA Finance | 3 | 4 |
| FIN-C04 | Credit Management | Sets customer credit limits and blocks orders of customers over their limit. | SAP S/4HANA Finance | 3 | 4 |
| FIN-C05 | Treasury and Cash Management | Manages bank accounts, payments, cash position and cash forecast. | Kyriba Treasury | 3 | 4 |
| FIN-C06 | Fixed Asset Accounting | Records fixed assets and computes depreciation. | SAP S/4HANA Finance | 4 | 4 |
| FIN-C07 | Management Accounting | Follows costs and margins by cost centre, profit centre and product line. | SAP S/4HANA Finance, Orvanne Data Platform | 3 | 4 |
| FIN-C08 | Financial Close and Consolidation | Closes the books each month, reconciles accounts and consolidates the group. | BlackLine Financial Close, SAP S/4HANA Finance | 2 | 4 |
| FIN-C09 | Tax and Statutory Reporting | Produces value-added tax returns, statutory accounts and the electronic invoicing reports required by law. | SAP S/4HANA Finance, Esker Invoice Platform | 3 | 4 |
| FIN-C10 | Travel and Expense Management | Captures, approves and reimburses employee expenses. | SAP Concur Expense | 4 | 4 |
| FIN-C11 | Inventory Valuation | Values the stock held in the distribution centre and posts goods movements to the ledger. | SAP S/4HANA Finance | 3 | 3 |

The largest gap is Financial Close and Consolidation (current 2, target 4): the monthly close takes eight working days, mostly because the trial balance of Orvanne Iberia arrives by file from Sage X3 Iberia and is re-entered by hand for intercompany items. The Fast Close project and the Iberia Finance Rollout project address this gap (section 11).

## 4. Application architecture

### 4.1 SAP S/4HANA Finance

| Item | Value |
|---|---|
| Name | SAP S/4HANA Finance |
| Acronym | S4F |
| Kind | Business application |
| Description | The accounting system of Orvanne Group. It keeps the general ledger, the sub-ledgers (customers, suppliers, fixed assets), management accounting, credit management and inventory valuation for company codes FR01, FR10 and DE20, and produces the legal customer invoices from the billing requests sent by the Salesforce Order Platform. |
| Version | SAP S/4HANA 2023 FPS02 |
| Lifecycle status | In production since 6 January 2025 |
| Hosting model | Private cloud (RISE with SAP, S/4HANA Cloud Private Edition, on Microsoft Azure) |
| Hosted at | Azure West Europe (production), Azure North Europe (disaster recovery) |
| Business owner | Finance Department |
| Vendor | SAP SE |
| Users | 310 named users |
| Annual cost | 1,850,000 euros (subscription, hosting and application maintenance) |

### 4.2 Components of SAP S/4HANA Finance

| Component | Kind | Layer | Description | Technologies | Hosted on |
|---|---|---|---|---|---|
| General Ledger (FI-GL) | Module | Finance core | Universal journal, chart of accounts ORVN, parallel ledgers for French GAAP and IFRS. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Accounts Payable (FI-AP) | Module | Finance core | Supplier open items, automatic payment run, withholding. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Accounts Receivable (FI-AR) | Module | Finance core | Customer open items, dunning, incoming payment clearing. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Asset Accounting (FI-AA) | Module | Finance core | Fixed asset register and depreciation runs. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Controlling (CO) | Module | Finance core | Cost centres, profit centres, margin analysis. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Credit Management (FSCM-CR) | Module | Finance core | Credit limits, credit exposure and credit blocks per business partner. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Billing (SD-BIL) | Module | Logistics, reduced scope | Creates the billing document (the legal customer invoice) and the credit memo from requests received from the Salesforce Order Platform. No sales order is entered in SAP. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Inventory Valuation (MM-IM) | Module | Logistics, reduced scope | Material master, valuated stock, goods movement postings received from Reflex WMS. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| Group Reporting | Module | Finance core | Consolidation of the group, intercompany eliminations. | ABAP Platform 2023 | s4p-app-01, s4p-app-02, s4p-app-03 |
| SAP HANA Database | Database | Data | In-memory database of the production system (system identifier S4P). | SAP HANA 2.0 SPS07 | s4p-hana-01 (replicated to s4r-hana-01) |
| SAP Fiori Launchpad | User interface | Presentation | Web user interface for all finance users. | SAP Fiori, SAPUI5 | s4p-wd-01, s4p-wd-02 |
| SAP Gateway OData Services | Service | Integration | Exposes the OData and SOAP APIs called by the Orvanne Integration Hub and SAP Integration Suite. | OData V4, SOAP | s4p-app-01, s4p-app-02, s4p-app-03 |
| Finance Extensions on BTP | Service | Extension | Side-by-side extensions (credit approval workflow, billing request monitor) built on SAP Business Technology Platform. | SAP BTP ABAP Environment, SAP Build Process Automation | SAP BTP subaccount orvanne-prod (region eu20) |
| Nightly Finance Jobs | Batch job | Batch | Scheduled jobs: payment run F110, dunning run, depreciation, foreign currency valuation, data extraction. | ABAP Platform 2023 | s4p-app-03 |

### 4.3 Satellite applications

A satellite application is an application system that exchanges data with SAP S/4HANA Finance. The figure shows them around the accounting block; the labels are the identifiers of the data exchanges of section 5.

```context
center: SAP S/4HANA Finance
left: Salesforce Order Platform | O2C-01 to O2C-05
left: Esker Invoice Platform | FIN-01, FIN-02, FIN-14, FIN-15
left: Kyriba Treasury | FIN-03, FIN-04
left: SAP Concur Expense | FIN-06, FIN-07
left: BlackLine Financial Close | FIN-09
left: ADP Payroll | FIN-08
left: Adyen Payments | O2C-06
left: OrderDesk | O2C-08
right: Reflex WMS | FIN-12
right: Akeneo PIM | FIN-16
right: Orvanne Data Platform | FIN-10
right: OpenText Archive Center | FIN-13
right: Sage X3 Iberia | FIN-11
right: Generix EDI Services | O2C-07
right: Microsoft Entra ID | single sign-on
caption: Figure 1. Application context of SAP S/4HANA Finance: satellite applications and exchange identifiers. Every exchange passes through an integration platform (section 4.4).
```

| Application system | Acronym | Kind | Purpose | Vendor | Hosting model | Lifecycle status | Business owner | Users |
|---|---|---|---|---|---|---|---|---|
| Salesforce Order Platform | SOP | Business application | Order management block: customer accounts, quotes, orders, fulfilment orchestration, customer service. Described in ORV-ARC-O2C-002. | Salesforce | SaaS | In production | Sales and Customer Operations | 620 |
| Esker Invoice Platform | | Business application | Captures supplier invoices (paper, PDF and electronic), runs the approval workflow, and exchanges electronic invoices with the customers' and suppliers' platforms as an accredited platform. | Esker | SaaS | In production | Finance Department | 140 |
| Kyriba Treasury | | Business application | Payment factory, bank connectivity, cash position and cash forecast. Only system allowed to talk to the banks. | Kyriba | SaaS | In production | Finance Department | 12 |
| SAP Concur Expense | | Business application | Expense reports of employees: capture, approval, reimbursement. | SAP SE | SaaS | In production | Finance Department | 1,400 |
| BlackLine Financial Close | | Business application | Account reconciliation and close task management. | BlackLine | SaaS | In production | Finance Department | 45 |
| ADP Payroll | | External system | Payroll of the French and German employees, run by ADP as a service. | ADP | SaaS | In production | Finance Department | 8 |
| Reflex WMS | WMS | Business application | Warehouse management of the Saint-Priest Distribution Centre: receiving, storage, picking, shipping. | Hardis Group | On-premise | In production | Sales and Customer Operations | 180 |
| Akeneo PIM | PIM | Business application | Product information management: descriptions, images and attributes of the 12,000 products sold. | Akeneo | SaaS | In production | Sales and Customer Operations | 25 |
| Orvanne Data Platform | ODP | Data platform | Data warehouse and reporting: Snowflake for storage, Microsoft Power BI for dashboards. | Snowflake | Public cloud | In production | Orvanne Group IT | 260 |
| OpenText Archive Center | | Technical platform | Legal archive of customer and supplier invoices, kept for ten years. | OpenText | On-premise | In production | Finance Department | 30 |
| Sage X3 Iberia | | Business application | Accounting system of Orvanne Iberia SL. To be replaced by SAP S/4HANA Finance (company code ES30) by the Iberia Finance Rollout project. | Sage | On-premise | Legacy | Finance Department | 22 |
| Adyen Payments | | External system | Payment service provider of the web shop; settles card payments to the bank and reports them. | Adyen | SaaS | In production | Sales and Customer Operations | 6 |
| Generix EDI Services | | Integration platform | EDI network for large customers: translates and routes EDIFACT messages. | Generix Group | SaaS | In production | Sales and Customer Operations | 5 |
| OrderDesk | ODK | Business application | Legacy order entry application developed in-house in 2009, being replaced by the Salesforce Order Platform. Still sends the shipped orders of Orvanne Deutschland GmbH for invoicing. Described in ORV-ARC-O2C-002. | Orvanne Group IT (in-house) | On-premise | Decommissioning | Sales and Customer Operations | 48 |
| House Bank EBICS Servers | | External system | The EBICS servers of the group's four house banks. Reached by Kyriba Treasury only. | | | In production | | |
| Public Invoicing Portal | PPF | External system | The French tax administration's portal, which holds the directory of invoice recipients and receives invoicing data. Reached by the Esker Invoice Platform only. Not described in this document. | | | In production | | |
| Orvanne HR Core | | Business application | Master of employee data. Referenced by FIN-07; not described in any architecture document yet. | | | In production | | |
| Microsoft Entra ID | | Technical platform | Identity provider for single sign-on and user provisioning. | Microsoft | SaaS | In production | Orvanne Group IT | 2,100 |

### 4.4 Integration platforms

Following the principle *No Point-to-Point Integration*, no satellite connects to SAP S/4HANA Finance directly. Three integration platforms carry the exchanges.

| Application system | Acronym | Kind | Purpose | Vendor | Hosting model | Lifecycle status | Business owner |
|---|---|---|---|---|---|---|---|
| Orvanne Integration Hub | OIH | Integration platform | The group's integration platform for APIs and events, built on MuleSoft Anypoint Platform. Carries every exchange between the two blocks and most exchanges with non-SAP satellites. | Salesforce (MuleSoft) | Public cloud | In production | Orvanne Group IT |
| SAP Integration Suite | CPI | Integration platform | Integration platform delivered by SAP on SAP Business Technology Platform. Restricted to packaged SAP-to-SAP integrations (SAP Concur Expense) and to the outbound connection from the private cloud to the Orvanne Integration Hub. | SAP SE | Public cloud | In production | Orvanne Group IT |
| MFT Gateway | MFT | Integration platform | Managed file transfer gateway for file exchanges over SFTP, built on GoAnywhere MFT. | Fortra | On-premise | In production | Orvanne Group IT |

### 4.5 Data ownership

Following the principle *One Master per Data Object*, the table gives the master system of each data object the accounting block handles.

| Data object | Description | Sensitivity | Master system |
|---|---|---|---|
| General Ledger Account | An account of the chart of accounts ORVN. | Internal | SAP S/4HANA Finance |
| Journal Entry | An accounting document in the universal journal. | Confidential | SAP S/4HANA Finance |
| Cost Centre | A cost centre or profit centre of management accounting. | Internal | SAP S/4HANA Finance |
| Customer Invoice | The legal invoice issued to a customer, with its PDF and electronic forms. | Confidential | SAP S/4HANA Finance |
| Customer Credit Profile | Credit limit, credit exposure, risk class and credit block of a customer. | Confidential | SAP S/4HANA Finance |
| Customer Payment | A payment received from a customer and its clearing against invoices. | Confidential | SAP S/4HANA Finance |
| Supplier | A supplier with its bank details and payment terms. | Confidential | SAP S/4HANA Finance |
| Supplier Invoice | An invoice received from a supplier. | Confidential | Esker Invoice Platform until posting, then SAP S/4HANA Finance |
| Material | A product as an accounting object: material number, valuation class, standard cost. | Internal | SAP S/4HANA Finance |
| Fixed Asset | A fixed asset and its depreciation. | Internal | SAP S/4HANA Finance |
| Customer Account | A customer as a commercial object: name, addresses, contacts, segment. | Confidential (personal data) | Salesforce Order Platform |
| Sales Order | A customer order and its lines. | Confidential | Salesforce Order Platform |
| Bank Statement | The statement of a bank account for one day. | Confidential | Kyriba Treasury |
| Payment Order | An outgoing payment instruction to a bank. | Highly confidential | Kyriba Treasury after release, SAP S/4HANA Finance before |
| Expense Report | An employee's expense report. | Confidential (personal data) | SAP Concur Expense |
| Goods Movement | A receipt, issue or transfer of stock in the distribution centre. | Internal | Reflex WMS |
| Employee | An employee of the group. | Confidential (personal data) | Orvanne HR Core |
| Product | A product as a commercial object: description, images, attributes. | Public | Akeneo PIM |

## 5. Data exchanges

### 5.1 Catalogue of exchanges

Twenty-four data exchanges involve the accounting block. The first table gives the source, the target, the mechanism and the frequency; the second gives the protocol, the format, the volume and the data objects carried. Unless stated otherwise an exchange is one-way.

| Exchange | Source | Target | Mechanism | Carried by | Frequency |
|---|---|---|---|---|---|
| O2C-01 Customer Account Synchronisation | Salesforce Order Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each change, near real time |
| O2C-02 Customer Credit Status | SAP S/4HANA Finance | Salesforce Order Platform | REST API | Orvanne Integration Hub | Every 15 minutes |
| O2C-03 Billing Request | Salesforce Order Platform | SAP S/4HANA Finance | Message queue | Orvanne Integration Hub | On each shipment confirmation, near real time |
| O2C-04 Invoice and Payment Status | SAP S/4HANA Finance | Salesforce Order Platform | Message queue | Orvanne Integration Hub | On each posting, near real time |
| O2C-05 Credit Memo Request | Salesforce Order Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each approved return |
| O2C-06 Web Shop Payment Settlement | Adyen Payments | SAP S/4HANA Finance | File transfer | MFT Gateway | Daily at 05:00 |
| O2C-07 EDI Outbound Invoice | SAP S/4HANA Finance | Generix EDI Services | EDI | Orvanne Integration Hub | On each invoice to an EDI customer |
| O2C-08 Legacy Order Billing File | OrderDesk | SAP S/4HANA Finance | File transfer | MFT Gateway | Daily at 23:00 |
| FIN-01 Supplier Invoice Posting | Esker Invoice Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each approved invoice |
| FIN-02 Supplier and Purchase Order Master Data | SAP S/4HANA Finance | Esker Invoice Platform | Batch extract | Orvanne Integration Hub | Every hour |
| FIN-03 Payment Run File | SAP S/4HANA Finance | Kyriba Treasury | File transfer | MFT Gateway | Twice a week (Tuesday and Thursday at 14:00) |
| FIN-04 Bank Statement Import | Kyriba Treasury | SAP S/4HANA Finance | File transfer | MFT Gateway | Daily at 07:30 |
| FIN-05 Bank Payment Transmission | Kyriba Treasury | House Bank EBICS Servers | File transfer | Kyriba Treasury (direct, EBICS) | After each approved payment batch |
| FIN-06 Expense Report Posting | SAP Concur Expense | SAP S/4HANA Finance | Web service | SAP Integration Suite | Daily at 22:00 |
| FIN-07 Cost Object and Employee Master Data | SAP S/4HANA Finance | SAP Concur Expense | Web service | SAP Integration Suite | Daily at 06:00 |
| FIN-08 Payroll Journal | ADP Payroll | SAP S/4HANA Finance | File transfer | MFT Gateway | Monthly, on the 26th |
| FIN-09 General Ledger Balances for Reconciliation | SAP S/4HANA Finance | BlackLine Financial Close | Batch extract | Orvanne Integration Hub | Daily at 02:00 |
| FIN-10 Finance Data Extract | SAP S/4HANA Finance | Orvanne Data Platform | Batch extract | Orvanne Integration Hub | Daily at 01:00 |
| FIN-11 Iberia Trial Balance Upload | Sage X3 Iberia | SAP S/4HANA Finance | Manual | E-mail, then manual upload | Monthly, on working day 3 |
| FIN-12 Goods Movement Posting | Reflex WMS | SAP S/4HANA Finance | Message queue | Orvanne Integration Hub | On each movement, near real time |
| FIN-13 Invoice Archiving | SAP S/4HANA Finance | OpenText Archive Center | Web service | SAP ArchiveLink through SAP Cloud Connector | On each invoice |
| FIN-14 Electronic Invoice Issuance | SAP S/4HANA Finance | Esker Invoice Platform | REST API | Orvanne Integration Hub | On each customer invoice |
| FIN-15 Electronic Invoice Lifecycle Status | Esker Invoice Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each status change |
| FIN-16 Material Master Distribution | SAP S/4HANA Finance | Akeneo PIM | REST API | Orvanne Integration Hub | On each material creation or change |

| Exchange | Protocol | Format | Volume | Data objects |
|---|---|---|---|---|
| O2C-01 Customer Account Synchronisation | HTTPS, OData V4 | JSON | 900 changes per day | Customer Account |
| O2C-02 Customer Credit Status | HTTPS, REST | JSON | 2,500 records per run | Customer Credit Profile |
| O2C-03 Billing Request | Anypoint MQ, then HTTPS OData V4 | JSON | 450 requests per day, 1,900 at peak | Sales Order |
| O2C-04 Invoice and Payment Status | Anypoint MQ, then HTTPS REST | JSON | 800 events per day | Customer Invoice, Customer Payment |
| O2C-05 Credit Memo Request | HTTPS, OData V4 | JSON | 35 requests per day | Sales Order |
| O2C-06 Web Shop Payment Settlement | SFTP | CSV (Adyen settlement detail report) | 1 file per day, 600 lines | Customer Payment |
| O2C-07 EDI Outbound Invoice | AS2 | EDIFACT INVOIC D96A | 140 invoices per day | Customer Invoice |
| O2C-08 Legacy Order Billing File | SFTP | CSV | 1 file per day, 120 orders | Sales Order |
| FIN-01 Supplier Invoice Posting | HTTPS, OData V4 | JSON with PDF attachment | 260 invoices per day | Supplier Invoice |
| FIN-02 Supplier and Purchase Order Master Data | HTTPS, REST | JSON | 300 records per run | Supplier, General Ledger Account, Cost Centre |
| FIN-03 Payment Run File | SFTP | ISO 20022 pain.001.001.09 (XML) | 2 files per week, 1,200 payments each | Payment Order |
| FIN-04 Bank Statement Import | SFTP | ISO 20022 camt.053.001.08 (XML) | 14 files per day (one per bank account) | Bank Statement |
| FIN-05 Bank Payment Transmission | EBICS 3.0 (TS profile) | ISO 20022 pain.001.001.09 (XML) | 3 batches per week | Payment Order |
| FIN-06 Expense Report Posting | HTTPS, SOAP | XML | 220 reports per day | Expense Report, Journal Entry |
| FIN-07 Cost Object and Employee Master Data | HTTPS, SOAP | XML | 2,300 records per run | Cost Centre, Employee |
| FIN-08 Payroll Journal | SFTP | Fixed-width text file | 2 files per month, 4,000 lines each | Journal Entry |
| FIN-09 General Ledger Balances for Reconciliation | HTTPS, REST | CSV | 18,000 balances per run | General Ledger Account, Journal Entry |
| FIN-10 Finance Data Extract | HTTPS, OData V4 (CDS views) | Parquet | 1.2 million lines per run | Journal Entry, Customer Invoice, Cost Centre, Material |
| FIN-11 Iberia Trial Balance Upload | E-mail | Microsoft Excel workbook | 1 file per month, 900 lines | General Ledger Account |
| FIN-12 Goods Movement Posting | Anypoint MQ, then HTTPS OData V4 | JSON | 6,500 movements per day | Goods Movement, Material |
| FIN-13 Invoice Archiving | HTTPS, SAP ArchiveLink | PDF/A-3 | 720 documents per day | Customer Invoice, Supplier Invoice |
| FIN-14 Electronic Invoice Issuance | HTTPS, REST | Factur-X 1.0.07 (PDF/A-3 with XML) | 450 invoices per day | Customer Invoice |
| FIN-15 Electronic Invoice Lifecycle Status | HTTPS, REST (webhook) | JSON | 1,300 status events per day | Customer Invoice |
| FIN-16 Material Master Distribution | HTTPS, REST | JSON | 40 materials per day | Material |

### 5.2 Order-to-cash exchanges with the Salesforce Order Platform

The order-to-cash process crosses both blocks. The Salesforce Order Platform captures the order and orchestrates its fulfilment; SAP S/4HANA Finance decides whether the customer may be delivered on credit, issues the legal invoice and collects the payment. No sales order exists in SAP: the first SAP object of the process is the billing document.

**O2C-01 Customer Account Synchronisation.** When a sales administrator creates or changes a customer account in the Salesforce Order Platform, the Orvanne Integration Hub calls the Business Partner OData API of SAP S/4HANA Finance and creates or updates the business partner in the customer role. Salesforce sends the commercial data (name, legal identifiers, addresses, invoicing contact). SAP adds the financial data, which Salesforce never changes: reconciliation account, payment terms, dunning procedure. SAP returns the business partner number, which Salesforce stores on the account.

**O2C-02 Customer Credit Status.** Every 15 minutes the Orvanne Integration Hub reads from SAP Credit Management the credit profiles changed since the previous run and updates the corresponding accounts in the Salesforce Order Platform. An order of a blocked customer, or an order that would exceed the available credit, is held in Salesforce for a credit controller's decision. The exchange is deliberately not real time: credit exposure is recomputed in SAP by a job that runs every ten minutes.

**O2C-03 Billing Request.** When Reflex WMS confirms a shipment, the Salesforce Order Platform publishes a billing request on the queue `o2c.billing-request` of the Orvanne Integration Hub. The hub calls SAP, which creates the billing document, posts it to accounts receivable and the general ledger, and triggers FIN-13 (archiving) and FIN-14 (electronic invoice). A request that SAP rejects (unknown business partner, closed posting period, missing tax code) stays on the dead-letter queue `o2c.billing-request.dlq` and appears in the billing request monitor of the Finance Extensions on BTP.

**O2C-04 Invoice and Payment Status.** SAP S/4HANA Finance publishes a business event when a billing document is posted and when a customer payment is cleared. The Orvanne Integration Hub forwards the event to the Salesforce Order Platform, which shows the invoice number, the invoice PDF link, the due date and the payment status on the order and in the customer portal.

**O2C-05 Credit Memo Request.** When a customer service agent approves a return or a commercial gesture in the Salesforce Order Platform, the Orvanne Integration Hub creates a credit memo request in SAP. A finance controller releases the requests above 2,000 euros.

**O2C-06 Web Shop Payment Settlement.** Card payments taken on the web shop are authorised by Adyen Payments (exchange CRM-07, described in ORV-ARC-O2C-002). Each morning Adyen deposits the settlement detail report on the MFT Gateway; a job of SAP S/4HANA Finance clears the customer invoices paid by card and posts the Adyen commission.

**O2C-07 EDI Outbound Invoice.** For the 65 customers who trade by EDI, SAP S/4HANA Finance sends the invoice as an IDoc to the Orvanne Integration Hub, which converts it to EDIFACT INVOIC D96A and sends it to Generix EDI Services. This exchange is in addition to FIN-14: the EDI message is a commercial copy, and the Factur-X invoice sent through the Esker Invoice Platform is the legal original.

**O2C-08 Legacy Order Billing File.** Until wave 3 of the Horizon O2C project goes live, the orders of Orvanne Deutschland GmbH are entered in the legacy application OrderDesk. Each night OrderDesk writes the orders shipped during the day to a CSV file, which the MFT Gateway delivers to SAP S/4HANA Finance; a job creates the billing documents in company code DE20. The exchange is temporary and stops on 1 March 2027.

#### Record layout of O2C-02 Customer Credit Status

| Position | Field | Data type | Length | Required | Description |
|---|---|---|---|---|---|
| 1 | businessPartnerId | String | 10 | Yes | SAP business partner number, the key shared with the Salesforce account. |
| 2 | creditSegment | String | 10 | Yes | SAP credit segment, always the company code (FR10 or DE20). |
| 3 | creditLimit | Decimal | 15 | Yes | Credit limit granted to the customer, in the currency of the segment. |
| 4 | creditExposure | Decimal | 15 | Yes | Open invoices plus open orders not yet invoiced. |
| 5 | currency | String | 3 | Yes | ISO 4217 currency code. |
| 6 | riskClass | String | 3 | Yes | Risk class from A (lowest risk) to E (highest risk). |
| 7 | creditBlocked | Boolean | 1 | Yes | True when a credit controller has blocked the customer. |
| 8 | blockReason | String | 40 | No | Reason of the block, filled when creditBlocked is true. |
| 9 | lastReviewDate | Date | 10 | No | Date of the last credit review, format YYYY-MM-DD. |
| 10 | changedAt | Timestamp | 24 | Yes | Date and time of the last change in SAP, in UTC. |

#### Record layout of O2C-04 Invoice and Payment Status

| Position | Field | Data type | Length | Required | Description |
|---|---|---|---|---|---|
| 1 | eventType | String | 20 | Yes | INVOICE_POSTED, INVOICE_CANCELLED or PAYMENT_CLEARED. |
| 2 | billingDocumentId | String | 10 | Yes | SAP billing document number, printed on the invoice. |
| 3 | salesforceOrderNumber | String | 12 | Yes | Order number of the Salesforce Order Platform, received in O2C-03. |
| 4 | businessPartnerId | String | 10 | Yes | SAP business partner number. |
| 5 | invoiceDate | Date | 10 | Yes | Invoice date, format YYYY-MM-DD. |
| 6 | dueDate | Date | 10 | Yes | Net due date. |
| 7 | netAmount | Decimal | 15 | Yes | Amount without tax. |
| 8 | taxAmount | Decimal | 15 | Yes | Value-added tax amount. |
| 9 | currency | String | 3 | Yes | ISO 4217 currency code. |
| 10 | paymentStatus | String | 12 | Yes | OPEN, PARTIALLY_PAID or PAID. |
| 11 | clearingDate | Date | 10 | No | Date the payment was cleared, filled for PAYMENT_CLEARED. |
| 12 | invoicePdfUrl | String | 255 | No | Link to the archived invoice in OpenText Archive Center. |

### 5.3 Exchanges with the finance satellites

**FIN-01 Supplier Invoice Posting and FIN-02 Supplier and Purchase Order Master Data.** The Esker Invoice Platform receives every supplier invoice, whatever its channel: electronic invoices from the suppliers' platforms, PDF files by e-mail, and scanned paper. It extracts the data, matches the invoice with the purchase order, and routes it for approval. Once approved, the invoice is posted in SAP accounts payable through FIN-01, with its image. To code invoices, Esker needs the suppliers, general ledger accounts, cost centres and open purchase orders, which it receives every hour through FIN-02.

**FIN-14 Electronic Invoice Issuance and FIN-15 Electronic Invoice Lifecycle Status.** Since 1 September 2026, customer invoices to French companies are issued as electronic invoices through an accredited platform. SAP S/4HANA Finance sends each customer invoice to the Esker Invoice Platform in Factur-X format (FIN-14). Esker looks up the recipient's platform in the directory of the Public Invoicing Portal, delivers the invoice, and sends the invoicing data to the tax administration. Lifecycle statuses (deposited, received, refused, paid) come back through FIN-15 and are stored on the billing document.

**FIN-03 Payment Run File, FIN-04 Bank Statement Import and FIN-05 Bank Payment Transmission.** SAP S/4HANA Finance never talks to a bank. The payment run proposes supplier payments and produces a pain.001 file, which the MFT Gateway delivers to Kyriba Treasury (FIN-03). Two treasurers approve the batch in Kyriba, which signs it and transmits it to the House Bank EBICS Servers (FIN-05). Each morning Kyriba collects the bank statements of the 14 bank accounts and delivers them to SAP as camt.053 files (FIN-04); SAP clears 82 percent of incoming customer payments automatically.

**FIN-06 Expense Report Posting and FIN-07 Cost Object and Employee Master Data.** These two exchanges use the packaged integration between SAP Concur Expense and SAP S/4HANA delivered by SAP on SAP Integration Suite. They are the only exchanges carried by SAP Integration Suite alone. The employee data sent to Concur comes from the Orvanne HR Core, which loads it into SAP as business partners in the employee role; that upstream load is not documented.

**FIN-08 Payroll Journal.** On the 26th of each month ADP Payroll deposits one journal file per company code (FR10, DE20) on the MFT Gateway. A job of SAP S/4HANA Finance posts it as a journal entry. The file is a fixed-width text file; its layout is below.

#### Record layout of FIN-08 Payroll Journal (detail record)

| Position | Field | Data type | Length | Required | Description |
|---|---|---|---|---|---|
| 1 | recordType | String | 1 | Yes | D for a detail record. The file starts with one header record (H) and ends with one trailer record (T) that carries the line count and the control total. |
| 2 | companyCode | String | 4 | Yes | SAP company code (FR10 or DE20). |
| 6 | postingDate | Date | 8 | Yes | Posting date, format YYYYMMDD. |
| 14 | glAccount | String | 10 | Yes | General ledger account of the chart of accounts ORVN, left-padded with zeros. |
| 24 | costCentre | String | 10 | No | Cost centre, required for expense accounts. |
| 34 | debitCreditIndicator | String | 1 | Yes | D for debit, C for credit. |
| 35 | amount | Decimal | 15 | Yes | Amount in cents, without sign, left-padded with zeros. |
| 50 | currency | String | 3 | Yes | Always EUR. |
| 53 | payrollPeriod | String | 6 | Yes | Payroll period, format YYYYMM. |
| 59 | itemText | String | 50 | No | Free text of the journal line. No employee name: payroll lines are aggregated by cost centre. |

**FIN-09 General Ledger Balances for Reconciliation.** Each night the Orvanne Integration Hub extracts the balances and open items of the balance sheet accounts and loads them into BlackLine Financial Close, where accountants reconcile and certify them.

**FIN-10 Finance Data Extract.** Each night the Orvanne Integration Hub extracts the day's journal entries, customer invoices and master data through released CDS views and loads them into the Orvanne Data Platform. Management reporting is done there, not in SAP.

**FIN-11 Iberia Trial Balance Upload.** Orvanne Iberia SL keeps its books in Sage X3 Iberia. On working day 3 of each month, the Madrid accountant exports the trial balance to an Excel workbook and sends it by e-mail to the consolidation team in Lyon, who map the accounts by hand and upload the file into Group Reporting. This is the only manual exchange of the accounting block and the only one that breaks the principle *No Point-to-Point Integration*. It disappears with the Iberia Finance Rollout project.

**FIN-12 Goods Movement Posting.** Reflex WMS publishes each goods receipt, goods issue and stock adjustment. The Orvanne Integration Hub posts it as a material document in SAP, which updates the value of the stock.

**FIN-13 Invoice Archiving.** Each customer invoice and each posted supplier invoice is stored in OpenText Archive Center through SAP ArchiveLink. Because the archive is on-premise and SAP is in the private cloud, the call goes through the SAP Cloud Connector installed in the Lyon Vénissieux Data Centre.

**FIN-16 Material Master Distribution.** A product is first created in SAP S/4HANA Finance as a material, which gives it its number and valuation class. The Orvanne Integration Hub sends the new material to Akeneo PIM, where the product managers enrich it before it is published to the Salesforce Order Platform (exchange CRM-01, described in ORV-ARC-O2C-002).

## 6. Infrastructure architecture

### 6.1 Sites

| Site | Kind | Location | Operator | Role |
|---|---|---|---|---|
| Azure West Europe | Cloud region | Amsterdam, Netherlands | Microsoft | Production of SAP S/4HANA Finance and of the Orvanne Data Platform |
| Azure North Europe | Cloud region | Dublin, Ireland | Microsoft | Disaster recovery of SAP S/4HANA Finance |
| SAP BTP Region eu20 | Cloud region | Amsterdam, Netherlands (on Azure) | SAP SE | SAP Integration Suite and Finance Extensions on BTP |
| MuleSoft CloudHub EU Frankfurt | Cloud region | Frankfurt, Germany | Salesforce | Runtime of the Orvanne Integration Hub |
| Lyon Vénissieux Data Centre | Data centre | Vénissieux, France | Orvanne Group IT | On-premise applications: MFT Gateway, OpenText Archive Center, SAP Cloud Connector, Reflex WMS servers |
| Saint-Priest Distribution Centre | Office site | Saint-Priest, France | Orvanne Group | Warehouse of 42,000 square metres; users and radio terminals of Reflex WMS |
| Lyon Headquarters | Office site | Lyon, France | Orvanne Group | Finance users |
| Madrid Office Server Room | Server room | Madrid, Spain | Orvanne Group IT | Server of Sage X3 Iberia |

### 6.2 Network zones

| Network zone | Site | Description |
|---|---|---|
| SAP Production VNet | Azure West Europe | Virtual network 10.40.0.0/20 of the SAP production system, managed by SAP under the RISE contract. No inbound access from the internet. |
| SAP Non-Production VNet | Azure West Europe | Virtual network 10.41.0.0/20 of the development and quality systems. |
| SAP Disaster Recovery VNet | Azure North Europe | Virtual network 10.42.0.0/20 of the standby system. |
| Lyon DMZ | Lyon Vénissieux Data Centre | Demilitarised zone 172.20.10.0/24 for the systems that exchange with external parties. |
| Lyon Internal Server Zone | Lyon Vénissieux Data Centre | Server zone 172.20.20.0/23, reachable from the office sites only. |
| CloudHub Private Space | MuleSoft CloudHub EU Frankfurt | Private space orvanne-prod-eu of the Orvanne Integration Hub, 10.60.0.0/22. |

The SAP Production VNet is connected to the Lyon Vénissieux Data Centre by an Azure ExpressRoute circuit of 500 megabits per second, with an IPsec VPN as backup. The CloudHub Private Space reaches SAP through an IPsec VPN to the Lyon Vénissieux Data Centre and then the ExpressRoute circuit; it never crosses the public internet.

### 6.3 Infrastructure nodes

| Node | Kind | Environment | Technology | Quantity | CPU | Memory (GB) | Storage (GB) | Network zone | Site |
|---|---|---|---|---|---|---|---|---|---|
| s4p-hana-01 | Virtual machine | Production | SUSE Linux Enterprise Server for SAP 15 SP5 | 1 | 96 | 1,024 | 4,096 | SAP Production VNet | Azure West Europe |
| s4p-app-01, s4p-app-02, s4p-app-03 | Virtual machine | Production | SUSE Linux Enterprise Server for SAP 15 SP5 | 3 | 16 | 128 | 256 | SAP Production VNet | Azure West Europe |
| s4p-wd-01, s4p-wd-02 | Virtual machine | Production | SAP Web Dispatcher 7.93 | 2 | 4 | 16 | 64 | SAP Production VNet | Azure West Europe |
| s4r-hana-01 | Virtual machine | Disaster recovery | SUSE Linux Enterprise Server for SAP 15 SP5 | 1 | 96 | 1,024 | 4,096 | SAP Disaster Recovery VNet | Azure North Europe |
| s4r-app-01 | Virtual machine | Disaster recovery | SUSE Linux Enterprise Server for SAP 15 SP5 | 1 | 16 | 128 | 256 | SAP Disaster Recovery VNet | Azure North Europe |
| s4q-hana-01 | Virtual machine | Preproduction | SUSE Linux Enterprise Server for SAP 15 SP5 | 1 | 48 | 512 | 2,048 | SAP Non-Production VNet | Azure West Europe |
| s4d-hana-01 | Virtual machine | Development | SUSE Linux Enterprise Server for SAP 15 SP5 | 1 | 32 | 256 | 1,024 | SAP Non-Production VNet | Azure West Europe |
| lyo-scc-01, lyo-scc-02 | Virtual machine | Production | SAP Cloud Connector 2.17 | 2 | 4 | 16 | 100 | Lyon DMZ | Lyon Vénissieux Data Centre |
| lyo-mft-01, lyo-mft-02 | Virtual machine | Production | GoAnywhere MFT 7.6 | 2 | 4 | 16 | 500 | Lyon DMZ | Lyon Vénissieux Data Centre |
| lyo-arc-01 | Virtual machine | Production | OpenText Archive Center 23.4 | 1 | 8 | 32 | 200 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| lyo-nas-02 | Storage array | Production | NetApp ONTAP 9.14 | 1 | | | 24,000 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| mad-x3-01 | Physical server | Production | Windows Server 2016 | 1 | 8 | 64 | 1,200 | | Madrid Office Server Room |

The SAP HANA Database of production runs on s4p-hana-01 and is replicated by HANA System Replication, in asynchronous mode, to s4r-hana-01 in Azure North Europe. The three application servers are load-balanced; Nightly Finance Jobs run on s4p-app-03 only. OpenText Archive Center stores its documents on the storage array lyo-nas-02. Sage X3 Iberia runs on the single physical server mad-x3-01, which has no standby: this is the main infrastructure risk of the accounting block (section 12).

## 7. Technology standards

| Technology | Version | Category | Vendor | Status |
|---|---|---|---|---|
| SAP S/4HANA | 2023 FPS02 | Business software | SAP SE | Standard |
| SAP HANA | 2.0 SPS07 | Database | SAP SE | Standard |
| ABAP Platform | 2023 | Language or framework | SAP SE | Standard |
| SAP Fiori | 3 | Language or framework | SAP SE | Standard |
| SAP Business Technology Platform | | Cloud service | SAP SE | Standard |
| SAP Integration Suite | | Middleware | SAP SE | Tolerated (SAP-to-SAP packaged content only) |
| SAP Cloud Connector | 2.17 | Middleware | SAP SE | Standard |
| MuleSoft Anypoint Platform | Mule runtime 4.6 | Middleware | Salesforce | Standard |
| Anypoint MQ | | Middleware | Salesforce | Standard |
| GoAnywhere MFT | 7.6 | Middleware | Fortra | Standard |
| SUSE Linux Enterprise Server for SAP | 15 SP5 | Operating system | SUSE | Standard |
| Microsoft Azure | | Cloud service | Microsoft | Standard |
| Azure ExpressRoute | | Network | Microsoft | Standard |
| Microsoft Entra ID | | Security | Microsoft | Standard |
| Snowflake | | Database | Snowflake | Standard |
| Microsoft Power BI | | Business software | Microsoft | Standard |
| OpenText Archive Center | 23.4 | Business software | OpenText | Tolerated |
| NetApp ONTAP | 9.14 | Storage and backup | NetApp | Standard |
| Sage X3 | Version 9 | Business software | Sage | Retiring |
| Windows Server 2016 | 2016 | Operating system | Microsoft | Retiring |
| SAP ECC | 6.0 EHP7 | Business software | SAP SE | Retired (replaced by SAP S/4HANA in January 2025) |
| OData | V4 | Standard or protocol | | Standard |
| ISO 20022 | pain.001.001.09, camt.053.001.08 | Standard or protocol | | Standard |
| EBICS | 3.0 | Standard or protocol | | Standard |
| Factur-X | 1.0.07 | Standard or protocol | | Standard |
| EDIFACT | D96A | Standard or protocol | | Tolerated |
| SAML | 2.0 | Standard or protocol | | Standard |
| SFTP | | Standard or protocol | | Tolerated (when the partner cannot offer an API) |
| TLS | 1.3 | Standard or protocol | | Standard |

## 8. Quality requirements

| Attribute | Requirement | Metric |
|---|---|---|
| Availability | SAP S/4HANA Finance is available to its users from Monday to Saturday, 06:00 to 22:00, Central European Time. | 99.7 percent per month over the service window |
| Availability | After the loss of Azure West Europe, SAP S/4HANA Finance restarts in Azure North Europe. | Recovery time objective 12 hours, recovery point objective 30 minutes |
| Performance | A Fiori screen opens fast enough for data entry work. | 95 percent of dialog steps under 1.5 seconds |
| Performance | A billing request received through O2C-03 becomes an invoice quickly enough for the driver's paperwork. | 95 percent of requests invoiced in under 2 minutes |
| Scalability | The system absorbs the end-of-month invoicing peak. | 1,900 billing requests per day, 60,000 journal entry lines per hour |
| Reliability | No billing request is lost between the two blocks. | Zero lost message; every rejected request is on the dead-letter queue within 5 minutes |
| Security | Duties are segregated: nobody can both create a supplier and pay it. | Zero unmitigated segregation-of-duties conflict at the quarterly review |
| Security | Payment files cannot be altered between SAP and the bank. | Every pain.001 file is signed (PGP) on the MFT Gateway and its hash is checked by Kyriba Treasury |
| Compliance | Customer and supplier invoices are archived in their original form for the legal period. | 10 years in OpenText Archive Center, in PDF/A-3 |
| Compliance | Customer invoices to French companies are issued through an accredited electronic invoicing platform. | 100 percent of domestic business invoices since 1 September 2026 |
| Compliance | The accounting entries file required by the French tax administration can be produced for any closed fiscal year. | File produced in under 4 hours |
| Maintainability | The core is kept clean so that the yearly upgrade stays cheap. | Zero modification of SAP standard objects; extensions on SAP BTP only |
| Interoperability | Exchanges use open standards when one exists. | ISO 20022 for payments, Factur-X for invoices, OData for APIs |

## 9. Security architecture

**Authentication.** Internal users reach the SAP Fiori Launchpad through single sign-on: SAP Cloud Identity Services delegates authentication to Microsoft Entra ID with SAML 2.0, and multi-factor authentication is required outside the office network. Technical users of the integration platforms authenticate with OAuth 2.0 client credentials and X.509 certificates, renewed every twelve months.

**Authorisation.** Roles are built per business capability (for example *Accounts Payable Accountant*, *Credit Controller*) and assigned through Entra ID groups. A quarterly review checks segregation-of-duties conflicts with SAP Cloud Identity Access Governance.

**Network.** SAP S/4HANA Finance has no internet-facing endpoint. Inbound calls arrive from the CloudHub Private Space and from the Lyon Vénissieux Data Centre over private links only. Outbound calls to SAP BTP use SAP Private Link.

**Data protection.** The database is encrypted at rest (HANA data volume encryption) and all exchanges use TLS 1.3. Bank details of suppliers are masked for users who do not need them. Personal data is limited to contact persons of customers and suppliers and to employees as payees of expense reports.

## 10. Architecture decisions

| Decision | Date | Rationale |
|---|---|---|
| FIN-AD-01: Host SAP S/4HANA Finance in the RISE with SAP private cloud on Microsoft Azure rather than on-premise. | March 2023 | The on-premise SAP ECC servers reached end of support in 2025. A private cloud keeps a single-tenant system that can hold the reduced logistics scope, while SAP operates the infrastructure. Azure was chosen because the Orvanne Data Platform and Microsoft Entra ID are already there. |
| FIN-AD-02: Convert SAP ECC to SAP S/4HANA by system conversion (brownfield), not by a new implementation. | March 2023 | Ten years of open items and asset history had to be kept, and the chart of accounts ORVN was already harmonised. A conversion took 14 months instead of an estimated 24. |
| FIN-AD-03: Keep no sales order in SAP; the Salesforce Order Platform sends billing requests. | November 2024 | Entering orders twice in two systems was the main cause of invoice disputes with OrderDesk. With one order in Salesforce and one invoice in SAP, each object has a single master (principle *One Master per Data Object*). |
| FIN-AD-04: Use the Orvanne Integration Hub for all exchanges, and SAP Integration Suite only for packaged SAP-to-SAP content. | November 2024 | Two general-purpose integration platforms would double skills and monitoring. SAP Integration Suite is kept for the SAP Concur Expense integration because SAP delivers and maintains it. |
| FIN-AD-05: Route all bank flows through Kyriba Treasury; remove the EBICS connection of SAP. | February 2026 | One payment factory gives the treasurers a single approval point and a single cash position for all entities, including Orvanne Iberia SL, which is not on SAP yet. |
| FIN-AD-06: Use the Esker Invoice Platform as the accredited electronic invoicing platform for both incoming and outgoing invoices. | June 2025 | Esker already captured supplier invoices. Choosing the same platform for issuance avoided a second vendor and a second connection to the Public Invoicing Portal. |
| FIN-AD-07: Do management reporting in the Orvanne Data Platform, not in SAP embedded analytics. | May 2025 | Margin analysis needs order data from the Salesforce Order Platform and finance data from SAP together. Only the data platform holds both. |

## 11. Roadmap and projects

| Project | Description | Sponsor | Status | Start | End | Budget (euros) | Systems affected |
|---|---|---|---|---|---|---|---|
| FINEO S/4HANA Migration | Converted SAP ECC 6.0 to SAP S/4HANA 2023 and moved it to the RISE with SAP private cloud. | Finance Department | Completed | 1 November 2023 | 6 January 2025 | 6,400,000 | SAP S/4HANA Finance, Orvanne Data Platform |
| Horizon O2C | Replaces the legacy order entry application OrderDesk with the Salesforce Order Platform and rebuilds the order-to-cash exchanges O2C-01 to O2C-05. | Sales and Customer Operations | In progress | 6 January 2025 | 31 March 2027 | 4,900,000 | Salesforce Order Platform, SAP S/4HANA Finance, Orvanne Integration Hub, Reflex WMS, OrderDesk |
| Payment Factory | Centralised all bank flows in Kyriba Treasury. | Finance Department | Completed | 1 September 2025 | 30 April 2026 | 620,000 | Kyriba Treasury, SAP S/4HANA Finance, MFT Gateway |
| E-Invoicing 2026 Compliance | Issues and receives electronic invoices through the Esker Invoice Platform, as required by French law from 1 September 2026. | Finance Department | Completed | 2 June 2025 | 1 September 2026 | 780,000 | SAP S/4HANA Finance, Esker Invoice Platform, Orvanne Integration Hub |
| Iberia Finance Rollout | Brings Orvanne Iberia SL into SAP S/4HANA Finance as company code ES30, connects it to the Spanish invoicing requirements, and decommissions Sage X3 Iberia. | Finance Department | In progress | 14 September 2026 | 30 June 2027 | 1,350,000 | SAP S/4HANA Finance, Sage X3 Iberia, Kyriba Treasury |
| Fast Close | Shortens the monthly close from eight to four working days: automatic intercompany matching, more reconciliations certified automatically in BlackLine Financial Close. | Finance Department | Planned | 4 January 2027 | 31 December 2027 | 540,000 | BlackLine Financial Close, SAP S/4HANA Finance |
| Archive to Cloud | Replaces the on-premise OpenText Archive Center with a cloud archive, in line with the principle *SaaS First*. | Orvanne Group IT | Planned | 1 July 2027 | 31 March 2028 | 300,000 | OpenText Archive Center, SAP S/4HANA Finance |

## 12. Risks and open points

1. **Sage X3 Iberia has no standby.** It runs on the single server mad-x3-01 in the Madrid Office Server Room, on Windows Server 2016 and Sage X3 version 9, both retiring. The risk is accepted until the Iberia Finance Rollout project ends on 30 June 2027.
2. **FIN-11 is manual.** The Iberia trial balance is mapped by hand each month. Two closings in 2026 were delayed by mapping errors.
3. **Dependency on the Lyon Vénissieux Data Centre.** Private-cloud SAP depends on three on-premise systems there: the SAP Cloud Connector, the MFT Gateway and OpenText Archive Center. The first two are doubled; lyo-arc-01 is not. If the archive is unavailable, invoices are queued in SAP and archived later.
4. **Credit status delay.** Between two runs of O2C-02, an order can be accepted in the Salesforce Order Platform for a customer who has just been blocked. The Finance Department accepts a delay of 15 minutes and has refused a longer one.
5. **Upstream employee data.** The load of employees from the Orvanne HR Core into SAP is not documented and has no named owner.

## 13. Glossary

| Term | Definition |
|---|---|
| Accredited platform | A private electronic invoicing platform registered by the French tax administration (*plateforme agréée*). |
| Billing document | The SAP object that represents a customer invoice. |
| Business partner | The SAP object that represents a customer, a supplier or an employee. |
| CDS view | Core Data Services view: the released data model through which SAP data is extracted. |
| Company code | The SAP object that represents a legal entity keeping its own books. |
| EBICS | Electronic Banking Internet Communication Standard, the bank communication protocol used in France and Germany. |
| O2C | Order to cash: the process from the customer order to the collected payment. |
| RISE with SAP | SAP's offering in which SAP operates S/4HANA in a private cloud on a public cloud provider. |
| Satellite application | An application system that exchanges data with one of the two main blocks. |
