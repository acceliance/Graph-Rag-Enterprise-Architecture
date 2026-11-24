---
title: Salesforce Order Platform Architecture Document
subtitle: Order management block of the Orvanne Group information system
---

## Document control

| Item | Value |
|---|---|
| Title | Salesforce Order Platform Architecture Document |
| Reference | ORV-ARC-O2C-002 |
| Version | 1.6 |
| Publication date | 26 October 2026 |
| Document type | Technical architecture document |
| Language | English |
| Status | Approved |
| Confidentiality | Internal, restricted to Orvanne Group and its integration partners |
| Issuer | Orvanne Group IT (the IT department of Orvanne Group) |
| Author | Thomas Girard, CRM and Commerce Solution Architect, Orvanne Group IT (thomas.girard@orvanne.example) |
| Reviewer | Nadia Benali, Enterprise Architect, Orvanne Group IT (nadia.benali@orvanne.example) |
| Approvers | Hugo Lemaire, Group Chief Information Officer, Orvanne Group IT; Sophie Marchetti, Chief Sales Officer, Sales and Customer Operations |

### Revision history

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 20 June 2025 | Thomas Girard | First issue: target architecture of the Horizon O2C project. |
| 1.2 | 16 February 2026 | Thomas Girard | Updated after the go-live of wave 1 (direct sales of Orvanne France SAS): order-to-cash exchanges O2C-01 to O2C-05 in production. |
| 1.4 | 11 May 2026 | Amélie Dupuis | Added the Orvanne Pro Shop (Salesforce B2B Commerce), Adyen Payments and the EDI exchanges with Generix EDI Services for wave 2. |
| 1.5 | 14 September 2026 | Thomas Girard | Added the transition architecture with OrderDesk for Orvanne Deutschland GmbH (exchanges CRM-14 and O2C-08). |
| 1.6 | 26 October 2026 | Thomas Girard | Updated after the go-live of wave 2 on 5 October 2026; added project44 Visibility and the MyOrvanne Portal Version 2 project. |

## 1. Purpose and scope

This document describes the architecture of the **Salesforce Order Platform**, the order management block of the Orvanne Group information system. It presents the system itself, its satellite applications, the data exchanges between them, the infrastructure it runs on, the technologies it uses, the quality requirements it must meet, the architecture decisions taken, and the projects that change it.

The information system of Orvanne Group is built around two main blocks:

- **Salesforce Order Platform**, for order management. It is the subject of this document.
- **SAP S/4HANA Finance**, for accounting. It is described in the *SAP S/4HANA Finance Architecture Document* (reference ORV-ARC-FIN-001).

The exchanges between the two blocks (the order-to-cash exchanges, prefixed O2C) are described in both documents, each from the point of view of its own block. Exchanges that involve only the order management block are prefixed CRM. Exchanges that involve only the accounting block are prefixed FIN and are described in ORV-ARC-FIN-001 only.

Out of scope: purchasing and supplier relations, transport planning (carriers are booked by the carriers' own portals), and the marketing website.

## 2. Enterprise context

### 2.1 Orvanne Group

Orvanne Group is a business-to-business distributor of commercial heating, ventilation and air-conditioning equipment and spare parts. Its head office is in Lyon, France. It sells 12,000 products to about 38,000 professional customers in France, Germany and Spain, through four sales channels.

| Sales channel | Share of order lines in 2025 | Order capture |
|---|---|---|
| Direct sales (field and inside sales representatives) | 46 percent | Quotes and orders entered in the Salesforce Order Platform |
| Web shop (Orvanne Pro Shop) | 27 percent | Orders placed by the customer in the Orvanne Pro Shop |
| EDI (65 large customers) | 21 percent | EDIFACT orders received through Generix EDI Services |
| Customer service (telephone and e-mail) | 6 percent | Orders entered by agents in the Salesforce Order Platform |

In 2025 the group took 95,000 orders, for 410,000 order lines. All orders are shipped from one warehouse, the Saint-Priest Distribution Centre.

### 2.2 Organisations involved

| Organisation | Kind | Role for the order management block |
|---|---|---|
| Orvanne Group | Business (the enterprise) | Owner of the information system |
| Orvanne Group IT | IT department | Operates the on-premise infrastructure, issues architecture documents, runs the integration platforms |
| Sales and Customer Operations | Business unit of Orvanne Group | Business owner of the Salesforce Order Platform and of its satellites |
| Finance Department | Business unit of Orvanne Group | Business owner of SAP S/4HANA Finance; decides credit limits |
| Salesforce | Vendor | Vendor of the Salesforce Order Platform, of MuleSoft Anypoint Platform and of Marketing Cloud Account Engagement |
| SAP SE | Vendor | Vendor of SAP S/4HANA Finance |
| Hardis Group | Vendor | Vendor of Reflex WMS |
| Akeneo | Vendor | Vendor of Akeneo PIM |
| Generix Group | Vendor | Vendor of Generix EDI Services |
| Adyen | Vendor | Payment service provider of the Orvanne Pro Shop |
| Dun & Bradstreet | Vendor | Provider of company identification and risk data |
| DocuSign | Vendor | Vendor of DocuSign eSignature |
| project44 | Vendor | Vendor of project44 Visibility |
| Genesys | Vendor | Vendor of Genesys Cloud CX |
| Microsoft | Vendor | Vendor of Microsoft Entra ID; hosting provider of the Orvanne Data Platform |
| Nexoria Digital | Vendor (integrator) | Integration partner for the Salesforce Order Platform and the Orvanne Integration Hub in the Horizon O2C project |

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

The Salesforce Order Platform and its satellites support three business areas: **Sales** (code BA-SAL), **Order Management** (code BA-ORD) and **Customer Service** (code BA-SRV). The table gives each business capability, the application system that supports it, and its maturity on the group's five-level scale (1 initial, 2 repeatable, 3 defined, 4 managed, 5 optimised) as assessed in June 2026, with the target for the end of 2027.

| Code | Business capability | Business area | Description | Supported by | Current maturity | Target maturity |
|---|---|---|---|---|---|---|
| SAL-C01 | Lead Management | Sales | Collects leads from marketing campaigns and qualifies them. | Marketing Cloud Account Engagement, Salesforce Order Platform | 3 | 4 |
| SAL-C02 | Customer Account Management | Sales | Keeps the customers, their sites, their contacts and their segmentation. | Salesforce Order Platform, D&B Direct+ | 4 | 4 |
| SAL-C03 | Opportunity Management | Sales | Follows sales opportunities from first contact to order. | Salesforce Order Platform | 4 | 4 |
| SAL-C04 | Quotation and Pricing | Sales | Builds quotes with customer-specific prices and discounts, and gets them signed. | Salesforce Order Platform, DocuSign eSignature | 3 | 4 |
| SAL-C05 | Product Information Management | Sales | Describes the products sold: texts, images, technical attributes, in three languages. | Akeneo PIM | 3 | 4 |
| ORD-C01 | Order Capture | Order Management | Records customer orders from the four sales channels in one place. | Salesforce Order Platform, Generix EDI Services | 3 | 5 |
| ORD-C02 | Order Orchestration | Order Management | Checks credit and stock, splits the order into fulfilment orders, and follows each step to invoicing. | Salesforce Order Platform | 3 | 4 |
| ORD-C03 | Order Fulfilment | Order Management | Picks, packs and ships the goods. | Reflex WMS | 4 | 4 |
| ORD-C04 | Delivery Tracking | Order Management | Tells the customer where the shipment is and when it arrives. | project44 Visibility, Salesforce Order Platform | 2 | 4 |
| ORD-C05 | Online Payment | Order Management | Takes card payments for web shop orders. | Adyen Payments | 3 | 3 |
| ORD-C06 | Returns Management | Order Management | Handles returns of goods and the resulting credit. | Salesforce Order Platform, Reflex WMS | 2 | 4 |
| SRV-C01 | Customer Service | Customer Service | Answers customer requests by telephone, e-mail and chat, and follows them as cases. | Salesforce Order Platform, Genesys Cloud CX | 3 | 4 |
| SRV-C02 | Customer Self-Service | Customer Service | Lets customers see their orders, invoices and cases without calling. | Salesforce Order Platform | 2 | 4 |

The largest gaps are Order Capture (current 3, target 5), because German orders are still entered in the legacy application OrderDesk; Delivery Tracking and Customer Self-Service (current 2, target 4), addressed by the MyOrvanne Portal Version 2 project; and Returns Management (current 2, target 4), addressed by the Returns Redesign project (section 11).

## 4. Application architecture

### 4.1 Salesforce Order Platform

| Item | Value |
|---|---|
| Name | Salesforce Order Platform |
| Acronym | SOP |
| Kind | Business application |
| Description | The order management system of Orvanne Group. It holds the customer accounts, the quotes and the orders of all sales channels, orchestrates the fulfilment of each order, and supports customer service. It is one Salesforce production organisation that combines several Salesforce products. |
| Version | Salesforce Winter '27 release |
| Lifecycle status | In production since 2 February 2026 (wave 1) |
| Hosting model | SaaS |
| Hosted at | Salesforce Hyperforce Germany |
| Business owner | Sales and Customer Operations |
| Vendor | Salesforce |
| Users | 620 internal users; 4,800 customer users of the web shop and the customer portal |
| Annual cost | 1,420,000 euros (subscriptions and application maintenance) |

### 4.2 Components of the Salesforce Order Platform

| Component | Kind | Layer | Description | Technologies |
|---|---|---|---|---|
| Sales Cloud | Module | Sales | Accounts, contacts, leads, opportunities, sales forecasts. | Salesforce Sales Cloud |
| Revenue Cloud Quoting | Module | Sales | Price books, customer-specific price agreements, quotes, discount approvals. | Salesforce Revenue Cloud |
| Order Management | Module | Order management | Order records, order orchestration flows, fulfilment orders, returns. | Salesforce Order Management |
| Orvanne Pro Shop | User interface | Channels | The business-to-business web shop, at shop.orvanne.example. | Salesforce B2B Commerce, Lightning Web Components |
| MyOrvanne Portal | User interface | Channels | The customer portal: orders, invoices, cases. | Salesforce Experience Cloud |
| Service Cloud | Module | Customer service | Cases, omni-channel routing, knowledge base, chat. | Salesforce Service Cloud |
| Credit Check Service | Service | Order management | Apex service that holds an order when the customer is blocked or over its credit limit, using the credit profile received through O2C-02. | Apex |
| Order Event Bus | Service | Integration | Platform events published at each step of an order (created, released, shipped, invoiced, paid), subscribed to by the Orvanne Integration Hub. | Salesforce Platform Events, Pub/Sub API |
| Salesforce Org Database | Database | Data | The multi-tenant database of the production organisation. | Salesforce Platform |
| Salesforce Shield | Infrastructure service | Security | Field encryption, event monitoring and field audit trail. | Salesforce Shield |
| Nightly Data Jobs | Batch job | Batch | Scheduled Apex jobs: price agreement expiry, stale quote clean-up, duplicate account detection. | Apex |

All components run on the Salesforce Hyperforce platform; Orvanne Group manages no server for them.

### 4.3 Satellite applications

A satellite application is an application system that exchanges data with the Salesforce Order Platform. The figure shows them around the order management block; the labels are the identifiers of the data exchanges of section 5.

```context
center: Salesforce Order Platform
left: SAP S/4HANA Finance | O2C-01 to O2C-05
left: Reflex WMS | CRM-02, CRM-03, CRM-04
left: Akeneo PIM | CRM-01
left: Generix EDI Services | CRM-05, CRM-06
left: Adyen Payments | CRM-07
left: OrderDesk | CRM-14
left: Orvanne Data Platform | CRM-12
right: D&B Direct+ | CRM-08
right: DocuSign eSignature | CRM-09
right: Marketing Cloud Account Engagement | CRM-10
right: project44 Visibility | CRM-11
right: Genesys Cloud CX | CRM-13
right: Microsoft Entra ID | CRM-15
caption: Figure 1. Application context of the Salesforce Order Platform: satellite applications and exchange identifiers. Exchanges on the left pass through the Orvanne Integration Hub; those on the right use connectors delivered by the vendors (section 4.4).
```

| Application system | Acronym | Kind | Purpose | Vendor | Hosting model | Lifecycle status | Business owner | Users |
|---|---|---|---|---|---|---|---|---|
| SAP S/4HANA Finance | S4F | Business application | Accounting block: customer credit, legal invoices, payments, general ledger. Described in ORV-ARC-FIN-001. | SAP SE | Private cloud | In production | Finance Department | 310 |
| Reflex WMS | WMS | Business application | Warehouse management of the Saint-Priest Distribution Centre: receiving, storage, picking, shipping. Master of stock levels and shipments. | Hardis Group | On-premise | In production | Sales and Customer Operations | 180 |
| Akeneo PIM | PIM | Business application | Product information management: descriptions, images and attributes of the 12,000 products sold. | Akeneo | SaaS | In production | Sales and Customer Operations | 25 |
| Generix EDI Services | | Integration platform | EDI network for the 65 large customers who trade by EDI: translates and routes EDIFACT messages. | Generix Group | SaaS | In production | Sales and Customer Operations | 5 |
| Adyen Payments | | External system | Payment service provider of the Orvanne Pro Shop: authorises and settles card payments. | Adyen | SaaS | In production | Sales and Customer Operations | 6 |
| D&B Direct+ | | External system | Company identification (D-U-N-S number, legal identifiers) and risk indicators, used to create clean customer accounts. | Dun & Bradstreet | SaaS | In production | Sales and Customer Operations | |
| DocuSign eSignature | | Business application | Electronic signature of quotes and framework agreements. | DocuSign | SaaS | In production | Sales and Customer Operations | 210 |
| Marketing Cloud Account Engagement | MCAE | Business application | Marketing automation: e-mail campaigns, forms, lead scoring. | Salesforce | SaaS | In production | Sales and Customer Operations | 14 |
| project44 Visibility | | External system | Collects tracking events from the 11 carriers and computes the estimated time of arrival. | project44 | SaaS | In production | Sales and Customer Operations | |
| Genesys Cloud CX | | Infrastructure system | Contact centre telephony of customer service: call routing, recording, screen pop. | Genesys | SaaS | In production | Sales and Customer Operations | 85 |
| Orvanne Data Platform | ODP | Data platform | Data warehouse and reporting: Snowflake for storage, Microsoft Power BI for dashboards. | Snowflake | Public cloud | In production | Orvanne Group IT | 260 |
| OrderDesk | ODK | Business application | Legacy order entry application developed in-house in 2009. Still used for the orders of Orvanne Deutschland GmbH until wave 3 of the Horizon O2C project; read-only for French orders since 5 October 2026. | Orvanne Group IT (in-house) | On-premise | Decommissioning | Sales and Customer Operations | 48 |
| Microsoft Entra ID | | Technical platform | Identity provider for single sign-on and user provisioning. | Microsoft | SaaS | In production | Orvanne Group IT | 2,100 |
| Carrier Booking Portals | | External system | The carriers' own portals, where the warehouse books transport. Referenced by Reflex WMS; not described in any architecture document. | | | In production | | |

### 4.4 Integration platforms

| Application system | Acronym | Kind | Purpose | Vendor | Hosting model | Lifecycle status | Business owner |
|---|---|---|---|---|---|---|---|
| Orvanne Integration Hub | OIH | Integration platform | The group's integration platform for APIs and events, built on MuleSoft Anypoint Platform. Carries every exchange between the two blocks and the exchanges with Reflex WMS, Akeneo PIM, Generix EDI Services, OrderDesk and the Orvanne Data Platform. | Salesforce (MuleSoft) | Public cloud | In production | Orvanne Group IT |
| MFT Gateway | MFT | Integration platform | Managed file transfer gateway for file exchanges over SFTP, built on GoAnywhere MFT. Used by the order management block for the OrderDesk files only. | Fortra | On-premise | In production | Orvanne Group IT |

The Orvanne Integration Hub follows the API-led approach in three layers. Its components are:

| Component of the Orvanne Integration Hub | Kind | Layer | Description | Hosted on |
|---|---|---|---|---|
| Experience APIs | Service | Experience | APIs shaped for one consumer: `x-salesforce-order-api`, `x-edi-partner-api`. | oih-prd-exp |
| Process APIs | Service | Process | APIs that orchestrate a business process across systems: `p-order-to-cash-api`, `p-customer-api`, `p-product-api`. | oih-prd-prc |
| System APIs | Service | System | One API per back-end system, hiding its protocol: `s-sap-finance-api`, `s-salesforce-api`, `s-reflex-wms-api`, `s-akeneo-api`, `s-generix-api`. | oih-prd-sys |
| Anypoint MQ Queues | Service | Messaging | Queues and exchanges for asynchronous flows, each with a dead-letter queue: `o2c.billing-request`, `o2c.invoice-status`, `wms.fulfilment-order`, `wms.shipment-confirmation`. | Anypoint MQ, region eu-central-1 |
| API Manager | Infrastructure service | Governance | Applies security and rate-limiting policies to every API and records the calls. | Anypoint control plane (European Union) |

Some satellites are connected by a connector that their vendor delivers and maintains for Salesforce, without passing through the Orvanne Integration Hub: DocuSign eSignature, Marketing Cloud Account Engagement, Genesys Cloud CX, D&B Direct+, project44 Visibility and Adyen Payments. The architecture board accepted these as exceptions to the principle *No Point-to-Point Integration* (decision CRM-AD-04).

### 4.5 Data ownership

Following the principle *One Master per Data Object*, the table gives the master system of each data object the order management block handles.

| Data object | Description | Sensitivity | Master system |
|---|---|---|---|
| Customer Account | A customer as a commercial object: name, legal identifiers, addresses, segment. | Confidential (personal data) | Salesforce Order Platform |
| Contact | A person working for a customer. | Confidential (personal data) | Salesforce Order Platform |
| Lead | A prospect not yet qualified. | Confidential (personal data) | Marketing Cloud Account Engagement until qualified, then Salesforce Order Platform |
| Opportunity | A sales opportunity with its amount and stage. | Confidential | Salesforce Order Platform |
| Quote | A priced offer to a customer. | Confidential | Salesforce Order Platform |
| Price Agreement | Customer-specific prices and discounts. | Highly confidential | Salesforce Order Platform |
| Sales Order | A customer order and its lines. | Confidential | Salesforce Order Platform (OrderDesk for German orders until wave 3) |
| Fulfilment Order | The part of an order sent to the warehouse for one shipment. | Internal | Salesforce Order Platform |
| Return Order | A return of goods requested by a customer. | Internal | Salesforce Order Platform |
| Service Case | A customer request followed by customer service. | Confidential (personal data) | Salesforce Order Platform |
| Product | A product as a commercial object: description, images, attributes. | Public | Akeneo PIM |
| Material | A product as an accounting object: material number, valuation class, standard cost. | Internal | SAP S/4HANA Finance |
| Stock Level | The quantity of a product available in the warehouse. | Internal | Reflex WMS |
| Shipment | A parcel or pallet shipped, with its carrier and tracking number. | Internal | Reflex WMS |
| Tracking Event | A carrier's event about a shipment. | Internal | project44 Visibility |
| Customer Credit Profile | Credit limit, credit exposure, risk class and credit block of a customer. | Confidential | SAP S/4HANA Finance |
| Customer Invoice | The legal invoice issued to a customer. | Confidential | SAP S/4HANA Finance |
| Customer Payment | A payment received from a customer. | Confidential | SAP S/4HANA Finance |
| Card Payment Authorisation | The authorisation of a card payment. No card number is stored by Orvanne Group. | Highly confidential | Adyen Payments |

## 5. Data exchanges

### 5.1 Catalogue of exchanges

Twenty-three data exchanges involve the order management block. The first table gives the source, the target, the mechanism and the frequency; the second gives the protocol, the format, the volume and the data objects carried. Unless stated otherwise an exchange is one-way.

| Exchange | Source | Target | Mechanism | Carried by | Frequency |
|---|---|---|---|---|---|
| O2C-01 Customer Account Synchronisation | Salesforce Order Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each change, near real time |
| O2C-02 Customer Credit Status | SAP S/4HANA Finance | Salesforce Order Platform | REST API | Orvanne Integration Hub | Every hour |
| O2C-03 Billing Request | Salesforce Order Platform | SAP S/4HANA Finance | Message queue | Orvanne Integration Hub | On each shipment confirmation, near real time |
| O2C-04 Invoice and Payment Status | SAP S/4HANA Finance | Salesforce Order Platform | Message queue | Orvanne Integration Hub | On each posting, near real time |
| O2C-05 Credit Memo Request | Salesforce Order Platform | SAP S/4HANA Finance | REST API | Orvanne Integration Hub | On each approved return |
| O2C-06 Web Shop Payment Settlement | Adyen Payments | SAP S/4HANA Finance | File transfer | MFT Gateway | Daily at 05:00 |
| O2C-07 EDI Outbound Invoice | SAP S/4HANA Finance | Generix EDI Services | EDI | Orvanne Integration Hub | On each invoice to an EDI customer |
| O2C-08 Legacy Order Billing File | OrderDesk | SAP S/4HANA Finance | File transfer | MFT Gateway | Daily at 23:00 |
| CRM-01 Product Catalogue Publication | Akeneo PIM | Salesforce Order Platform | REST API | Orvanne Integration Hub | On each product publication |
| CRM-02 Fulfilment Order Dispatch | Salesforce Order Platform | Reflex WMS | Message queue | Orvanne Integration Hub | On each order release, near real time |
| CRM-03 Shipment Confirmation | Reflex WMS | Salesforce Order Platform | Message queue | Orvanne Integration Hub | On each shipment, near real time |
| CRM-04 Stock Availability Feed | Reflex WMS | Salesforce Order Platform | REST API | Orvanne Integration Hub | Every 5 minutes |
| CRM-05 EDI Inbound Order | Generix EDI Services | Salesforce Order Platform | EDI | Orvanne Integration Hub | On each message |
| CRM-06 EDI Order Response and Despatch Advice | Salesforce Order Platform | Generix EDI Services | EDI | Orvanne Integration Hub | On each order confirmation and each shipment |
| CRM-07 Web Shop Payment Authorisation | Salesforce Order Platform | Adyen Payments | REST API | Adyen connector for Salesforce B2B Commerce | On each card payment (two-way) |
| CRM-08 Company Data Enrichment | D&B Direct+ | Salesforce Order Platform | REST API | D&B Connect for Salesforce | On each account creation, then monthly |
| CRM-09 Quote Electronic Signature | Salesforce Order Platform | DocuSign eSignature | REST API | DocuSign Apps Launcher for Salesforce | On each quote sent for signature (two-way) |
| CRM-10 Marketing Lead Synchronisation | Marketing Cloud Account Engagement | Salesforce Order Platform | Other (native connector) | Account Engagement connector | Every 2 minutes (two-way) |
| CRM-11 Shipment Tracking Events | project44 Visibility | Salesforce Order Platform | REST API | project44 webhook to a Salesforce REST endpoint | On each carrier event |
| CRM-12 CRM Data Extract | Salesforce Order Platform | Orvanne Data Platform | Batch extract | Orvanne Integration Hub | Daily at 00:30 |
| CRM-13 Telephony Screen Pop | Genesys Cloud CX | Salesforce Order Platform | Other (native connector) | Genesys Cloud for Salesforce | On each call |
| CRM-14 Order History Migration | OrderDesk | Salesforce Order Platform | Batch extract | Orvanne Integration Hub | Weekly on Sunday, until OrderDesk is decommissioned |
| CRM-15 User Provisioning | Microsoft Entra ID | Salesforce Order Platform | REST API | Entra ID provisioning service | Every 40 minutes |

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
| CRM-01 Product Catalogue Publication | HTTPS, REST | JSON | 150 products per day | Product |
| CRM-02 Fulfilment Order Dispatch | Anypoint MQ, then HTTPS REST | JSON | 480 fulfilment orders per day | Fulfilment Order |
| CRM-03 Shipment Confirmation | Anypoint MQ, then HTTPS REST | JSON | 470 confirmations per day | Shipment, Fulfilment Order |
| CRM-04 Stock Availability Feed | HTTPS, REST | JSON | 12,000 stock levels per run (changed levels only after the first run of the day) | Stock Level |
| CRM-05 EDI Inbound Order | AS2 | EDIFACT ORDERS D96A | 85 orders per day | Sales Order |
| CRM-06 EDI Order Response and Despatch Advice | AS2 | EDIFACT ORDRSP D96A and DESADV D96A | 170 messages per day | Sales Order, Shipment |
| CRM-07 Web Shop Payment Authorisation | HTTPS, REST | JSON | 600 payments per day | Card Payment Authorisation |
| CRM-08 Company Data Enrichment | HTTPS, REST | JSON | 40 accounts per day; 38,000 at the monthly refresh | Customer Account |
| CRM-09 Quote Electronic Signature | HTTPS, REST | JSON and PDF | 60 quotes per day | Quote |
| CRM-10 Marketing Lead Synchronisation | HTTPS | Proprietary | 1,100 records per day | Lead, Contact |
| CRM-11 Shipment Tracking Events | HTTPS, REST (webhook) | JSON | 3,800 events per day | Tracking Event, Shipment |
| CRM-12 CRM Data Extract | Salesforce Bulk API 2.0 | CSV, loaded as Parquet | 600,000 records per run | Customer Account, Opportunity, Quote, Sales Order, Service Case |
| CRM-13 Telephony Screen Pop | HTTPS, WebSocket | JSON | 1,400 calls per day | Service Case, Contact |
| CRM-14 Order History Migration | JDBC, then Salesforce Bulk API 2.0 | CSV | 2,400 orders per run | Sales Order |
| CRM-15 User Provisioning | HTTPS, SCIM 2.0 | JSON | 15 changes per day | (user accounts) |

### 5.2 Order-to-cash exchanges with SAP S/4HANA Finance

The order-to-cash process crosses both blocks. The Salesforce Order Platform captures the order and orchestrates its fulfilment; SAP S/4HANA Finance decides whether the customer may be delivered on credit, issues the legal invoice and collects the payment. The Salesforce order is the only order: SAP holds no sales order.

The steps of a standard order are:

1. The order is created in the Salesforce Order Platform (by a sales representative, the Orvanne Pro Shop, CRM-05 or a customer service agent).
2. The Credit Check Service checks the customer's credit profile, received from SAP through O2C-02. A blocked or over-limit order is held for a credit controller.
3. The order is released and split into fulfilment orders, sent to Reflex WMS through CRM-02.
4. Reflex WMS ships the goods and confirms through CRM-03.
5. The Salesforce Order Platform sends a billing request to SAP S/4HANA Finance through O2C-03.
6. SAP creates the invoice and returns its number and status through O2C-04. Later it returns the payment status the same way.

**O2C-01 Customer Account Synchronisation.** When a sales administrator creates or changes a customer account, the Order Event Bus publishes an event, and the process API `p-customer-api` of the Orvanne Integration Hub creates or updates the business partner in SAP S/4HANA Finance. SAP returns its business partner number, stored on the account in the field `SAP_Business_Partner_Id__c`. An account without this number cannot receive an order.

**O2C-02 Customer Credit Status.** Every hour the Orvanne Integration Hub reads from SAP S/4HANA Finance the credit profiles that changed and updates the accounts in the Salesforce Order Platform (fields credit limit, credit exposure, risk class, credit block). The Credit Check Service uses these fields; it never calls SAP during order entry, so that order capture keeps working when SAP is unavailable.

**O2C-03 Billing Request.** When a fulfilment order is confirmed as shipped, the Order Event Bus publishes an *order shipped* event. The process API `p-order-to-cash-api` builds the billing request and puts it on the queue `o2c.billing-request`; the system API `s-sap-finance-api` delivers it to SAP. If SAP rejects it, the message goes to the dead-letter queue `o2c.billing-request.dlq` and the order shows the status *Billing error* until a finance user corrects the cause and replays the message.

**O2C-04 Invoice and Payment Status.** The Orvanne Integration Hub receives the invoice and payment events of SAP S/4HANA Finance on the queue `o2c.invoice-status` and updates the order summary. The customer sees the invoice and its payment status in the MyOrvanne Portal.

**O2C-05 Credit Memo Request.** When a return order is received in the warehouse and approved by a customer service agent, or when an agent grants a commercial gesture, the Salesforce Order Platform asks SAP S/4HANA Finance for a credit memo.

**O2C-06 Web Shop Payment Settlement and O2C-07 EDI Outbound Invoice.** These two exchanges do not touch the Salesforce Order Platform but close the order-to-cash process for the web shop and EDI channels. Adyen Payments reports the settled card payments to SAP S/4HANA Finance each morning (O2C-06). SAP sends the invoices of EDI customers to Generix EDI Services (O2C-07). Both are detailed in ORV-ARC-FIN-001.

**O2C-08 Legacy Order Billing File.** During the transition, the orders of Orvanne Deutschland GmbH are still entered in OrderDesk. Each night OrderDesk writes the orders shipped during the day to a CSV file, which the MFT Gateway delivers to SAP S/4HANA Finance for invoicing in company code DE20. This exchange is the old way of working that O2C-03 replaces; it stops when wave 3 goes live.

#### Record layout of O2C-01 Customer Account Synchronisation

| Position | Field | Data type | Length | Required | Description |
|---|---|---|---|---|---|
| 1 | salesforceAccountId | String | 18 | Yes | Salesforce identifier of the account. |
| 2 | businessPartnerId | String | 10 | No | SAP business partner number. Empty on creation; returned by SAP. |
| 3 | legalName | String | 80 | Yes | Registered name of the company. |
| 4 | countryCode | String | 2 | Yes | ISO 3166 country code of the registered office. |
| 5 | vatNumber | String | 14 | Yes | Intra-community value-added tax number. |
| 6 | nationalCompanyId | String | 14 | Yes | SIRET number in France, Handelsregisternummer in Germany, NIF in Spain. |
| 7 | dunsNumber | String | 9 | No | D-U-N-S number from D&B Direct+. |
| 8 | billingStreet | String | 60 | Yes | Street of the invoicing address. |
| 9 | billingPostalCode | String | 10 | Yes | Postal code of the invoicing address. |
| 10 | billingCity | String | 40 | Yes | City of the invoicing address. |
| 11 | invoicingEmail | String | 120 | No | E-mail address that receives invoice notifications. |
| 12 | salesOrganisation | String | 4 | Yes | Selling entity: FR10 or DE20. |
| 13 | customerSegment | String | 20 | Yes | INSTALLER, FACILITY_MANAGER, CONTRACTOR or RESELLER. |
| 14 | requestedPaymentTerms | String | 4 | No | Payment terms negotiated by the sales representative; SAP applies them only after a credit controller's approval. |

#### Record layout of O2C-03 Billing Request

| Position | Field | Data type | Length | Required | Description |
|---|---|---|---|---|---|
| 1 | billingRequestId | String | 36 | Yes | Unique identifier of the request (UUID), used by SAP to ignore duplicates. |
| 2 | salesforceOrderNumber | String | 12 | Yes | Order number of the Salesforce Order Platform. |
| 3 | fulfilmentOrderNumber | String | 14 | Yes | Fulfilment order that was shipped. |
| 4 | businessPartnerId | String | 10 | Yes | SAP business partner number of the invoiced customer. |
| 5 | salesOrganisation | String | 4 | Yes | Selling entity: FR10 or DE20. |
| 6 | salesChannel | String | 10 | Yes | DIRECT, WEBSHOP, EDI or SERVICE. |
| 7 | customerPurchaseOrder | String | 35 | No | The customer's own purchase order number, printed on the invoice. |
| 8 | shipmentDate | Date | 10 | Yes | Date of the goods issue in Reflex WMS, format YYYY-MM-DD. |
| 9 | currency | String | 3 | Yes | ISO 4217 currency code. |
| 10 | lineNumber | Integer | 4 | Yes | Line number; the following fields repeat for each line. |
| 11 | materialNumber | String | 18 | Yes | SAP material number of the product. |
| 12 | quantity | Decimal | 13 | Yes | Quantity shipped. |
| 13 | unitOfMeasure | String | 3 | Yes | Unit of the quantity (PCE, BOX, MTR). |
| 14 | netUnitPrice | Decimal | 15 | Yes | Price per unit after discounts, without tax. Salesforce is the master of prices; SAP does not recalculate them. |
| 15 | taxCode | String | 2 | Yes | Value-added tax code, checked by SAP. |
| 16 | paymentReference | String | 24 | No | Adyen payment reference when the order was paid by card. |

### 5.3 Exchanges with the order management satellites

**CRM-01 Product Catalogue Publication.** A product is first created in SAP S/4HANA Finance as a material and sent to Akeneo PIM (exchange FIN-16, described in ORV-ARC-FIN-001). Product managers enrich it in Akeneo PIM. When they publish it, the Orvanne Integration Hub creates or updates the product in the Salesforce Order Platform, with its texts in French, German and Spanish and links to its images.

**CRM-02 Fulfilment Order Dispatch and CRM-03 Shipment Confirmation.** Each released fulfilment order is put on the queue `wms.fulfilment-order` and delivered to Reflex WMS. When the goods leave, Reflex WMS publishes the confirmation (quantities shipped, parcels, carrier, tracking numbers) on the queue `wms.shipment-confirmation`. A partial shipment produces one confirmation per shipment. Reflex WMS also posts the goods issue to SAP S/4HANA Finance (exchange FIN-12).

**CRM-04 Stock Availability Feed.** Every 5 minutes the Orvanne Integration Hub reads the available stock from Reflex WMS and updates the Salesforce Order Platform, so that sales representatives and the Orvanne Pro Shop promise only what is in stock.

**CRM-05 EDI Inbound Order and CRM-06 EDI Order Response and Despatch Advice.** Generix EDI Services receives the EDIFACT ORDERS messages of the 65 EDI customers and forwards them to the experience API `x-edi-partner-api`, which converts each message into an order in the Salesforce Order Platform. An order whose product code or price does not match is created with the status *To review*. The order confirmation (ORDRSP) and the despatch advice (DESADV) go back the same way.

**CRM-07 Web Shop Payment Authorisation.** At checkout the Orvanne Pro Shop shows the Adyen payment component. The card data goes from the customer's browser to Adyen Payments directly; the Salesforce Order Platform receives only a payment reference and the authorisation result.

**CRM-08 Company Data Enrichment.** When an account is created, D&B Direct+ returns the D-U-N-S number, the legal identifiers and the registered address, which prevents duplicate and misspelt accounts. All accounts are refreshed once a month.

**CRM-09 Quote Electronic Signature.** A quote above 15,000 euros, or a framework agreement, is sent to the customer for signature through DocuSign eSignature. The signed document comes back and is attached to the quote.

**CRM-10 Marketing Lead Synchronisation.** Marketing Cloud Account Engagement and the Salesforce Order Platform synchronise leads, contacts and campaign results through the connector delivered by Salesforce.

**CRM-11 Shipment Tracking Events.** project44 Visibility collects the events of the 11 carriers and sends them to the Salesforce Order Platform, which shows the delivery progress on the order.

**CRM-12 CRM Data Extract.** Each night the Orvanne Integration Hub extracts the accounts, opportunities, quotes, orders and cases changed during the day and loads them into the Orvanne Data Platform, where they are combined with the finance data received through FIN-10.

**CRM-13 Telephony Screen Pop.** When a customer calls, Genesys Cloud CX identifies the caller by telephone number and opens the customer's record for the agent.

**CRM-14 Order History Migration.** Each Sunday the Orvanne Integration Hub reads from the OrderDesk database the German orders closed during the week and loads them into the Salesforce Order Platform as historical orders, so that the history is complete on the day wave 3 goes live.

**CRM-15 User Provisioning.** Microsoft Entra ID creates, updates and deactivates the users of the Salesforce Order Platform from the membership of Entra ID groups.

## 6. Infrastructure architecture

### 6.1 Sites

| Site | Kind | Location | Operator | Role |
|---|---|---|---|---|
| Salesforce Hyperforce Germany | Provider data centre | Frankfurt, Germany | Salesforce | Production organisation and sandboxes of the Salesforce Order Platform |
| MuleSoft CloudHub EU Frankfurt | Cloud region | Frankfurt, Germany | Salesforce | Runtime of the Orvanne Integration Hub |
| Lyon Vénissieux Data Centre | Data centre | Vénissieux, France | Orvanne Group IT | On-premise applications: Reflex WMS, OrderDesk, MFT Gateway |
| Saint-Priest Distribution Centre | Office site | Saint-Priest, France | Orvanne Group | Warehouse of 42,000 square metres; users and radio terminals of Reflex WMS |
| Lyon Headquarters | Office site | Lyon, France | Orvanne Group | Sales administration and customer service (85 agents) |
| Düsseldorf Office | Office site | Düsseldorf, Germany | Orvanne Group | Sales administration of Orvanne Deutschland GmbH; users of OrderDesk |
| Azure West Europe | Cloud region | Amsterdam, Netherlands | Microsoft | Orvanne Data Platform; SAP S/4HANA Finance |

### 6.2 Network zones

| Network zone | Site | Description |
|---|---|---|
| CloudHub Private Space | MuleSoft CloudHub EU Frankfurt | Private space orvanne-prod-eu of the Orvanne Integration Hub, 10.60.0.0/22. |
| CloudHub Non-Production Private Space | MuleSoft CloudHub EU Frankfurt | Private space orvanne-nonprod-eu, 10.61.0.0/22, for development and acceptance. |
| Lyon DMZ | Lyon Vénissieux Data Centre | Demilitarised zone 172.20.10.0/24 for the systems that exchange with external parties. |
| Lyon Internal Server Zone | Lyon Vénissieux Data Centre | Server zone 172.20.20.0/23, reachable from the office sites only. |
| Saint-Priest Warehouse Zone | Saint-Priest Distribution Centre | Wireless network 172.21.0.0/22 of the radio terminals and label printers. |

The CloudHub Private Space is connected to the Lyon Vénissieux Data Centre by two IPsec VPN tunnels ending on the firewalls lyo-fw-01 and lyo-fw-02. The Salesforce Order Platform itself is reached over the internet with TLS; calls from the Orvanne Integration Hub to Salesforce leave from fixed addresses that Salesforce trusts. The Saint-Priest Distribution Centre is linked to the data centre by two fibre links of 1 gigabit per second from different operators.

### 6.3 Environments of the Salesforce Order Platform

| Environment | Kind | Salesforce organisation | Use |
|---|---|---|---|
| Production | Production | orvanne (production organisation) | Live system |
| UAT | Preproduction | orvanne--uat (full copy sandbox) | User acceptance, performance tests, training; refreshed every quarter |
| INT | Test | orvanne--int (partial copy sandbox) | Integration tests with the non-production Orvanne Integration Hub and the SAP quality system |
| DEV | Development | Developer sandboxes, one per team | Development |

### 6.4 Infrastructure nodes

| Node | Kind | Environment | Technology | Quantity | CPU | Memory (GB) | Storage (GB) | Network zone | Site |
|---|---|---|---|---|---|---|---|---|---|
| oih-prd-exp | Container host | Production | Mule runtime 4.6 | 4 replicas | 0.5 vCore each | 2 | | CloudHub Private Space | MuleSoft CloudHub EU Frankfurt |
| oih-prd-prc | Container host | Production | Mule runtime 4.6 | 4 replicas | 1 vCore each | 4 | | CloudHub Private Space | MuleSoft CloudHub EU Frankfurt |
| oih-prd-sys | Container host | Production | Mule runtime 4.6 | 6 replicas | 0.5 vCore each | 2 | | CloudHub Private Space | MuleSoft CloudHub EU Frankfurt |
| lyo-wms-app-01, lyo-wms-app-02 | Virtual machine | Production | Red Hat Enterprise Linux 8.10 | 2 | 8 | 32 | 200 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| lyo-wms-db-01, lyo-wms-db-02 | Physical server | Production | Oracle Database 19c | 2 | 16 | 128 | 2,000 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| lyo-odk-app-01 | Virtual machine | Production | Windows Server 2012 R2 | 1 | 4 | 16 | 120 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| lyo-odk-db-01 | Virtual machine | Production | Microsoft SQL Server 2014 | 1 | 8 | 64 | 800 | Lyon Internal Server Zone | Lyon Vénissieux Data Centre |
| lyo-mft-01, lyo-mft-02 | Virtual machine | Production | GoAnywhere MFT 7.6 | 2 | 4 | 16 | 500 | Lyon DMZ | Lyon Vénissieux Data Centre |
| lyo-fw-01, lyo-fw-02 | Network device | Production | Fortinet FortiGate 200F | 2 | | | | Lyon DMZ | Lyon Vénissieux Data Centre |
| spr-rf-terminals | End-user device | Production | Zebra MC9300 | 160 | | | | Saint-Priest Warehouse Zone | Saint-Priest Distribution Centre |

Reflex WMS has two components: its application server, hosted on lyo-wms-app-01 and lyo-wms-app-02 behind a load balancer, and its database, hosted on lyo-wms-db-01 with lyo-wms-db-02 as an Oracle Data Guard standby. OrderDesk has a web application on lyo-odk-app-01 and a database on lyo-odk-db-01; neither has a standby, and both run on products that their vendor no longer supports.

## 7. Technology standards

| Technology | Version | Category | Vendor | Status |
|---|---|---|---|---|
| Salesforce Sales Cloud | Winter '27 | Business software | Salesforce | Standard |
| Salesforce Service Cloud | Winter '27 | Business software | Salesforce | Standard |
| Salesforce Revenue Cloud | Winter '27 | Business software | Salesforce | Standard |
| Salesforce Order Management | Winter '27 | Business software | Salesforce | Standard |
| Salesforce B2B Commerce | Winter '27 | Business software | Salesforce | Standard |
| Salesforce Experience Cloud | Winter '27 | Business software | Salesforce | Standard |
| Salesforce Shield | | Security | Salesforce | Standard |
| Apex | API version 62.0 | Language or framework | Salesforce | Standard (when no declarative option exists) |
| Lightning Web Components | | Language or framework | Salesforce | Standard |
| Salesforce Platform Events | | Middleware | Salesforce | Standard |
| MuleSoft Anypoint Platform | Mule runtime 4.6 | Middleware | Salesforce | Standard |
| Anypoint MQ | | Middleware | Salesforce | Standard |
| GoAnywhere MFT | 7.6 | Middleware | Fortra | Standard |
| Reflex WMS | 9.2 | Business software | Hardis Group | Standard |
| Oracle Database | 19c | Database | Oracle | Tolerated (packaged software that requires it) |
| Red Hat Enterprise Linux | 8.10 | Operating system | Red Hat | Standard |
| Fortinet FortiGate | 200F | Network | Fortinet | Standard |
| Zebra MC9300 | | End-user device | Zebra Technologies | Standard |
| Microsoft Entra ID | | Security | Microsoft | Standard |
| Snowflake | | Database | Snowflake | Standard |
| Microsoft SQL Server | 2014 | Database | Microsoft | Retiring |
| Windows Server 2012 R2 | 2012 R2 | Operating system | Microsoft | Retiring |
| Microsoft .NET Framework | 4.5 | Language or framework | Microsoft | Retiring |
| OAuth | 2.0 | Standard or protocol | | Standard |
| SAML | 2.0 | Standard or protocol | | Standard |
| SCIM | 2.0 | Standard or protocol | | Standard |
| OData | V4 | Standard or protocol | | Standard |
| EDIFACT | D96A | Standard or protocol | | Tolerated |
| AS2 | | Standard or protocol | | Tolerated |
| SFTP | | Standard or protocol | | Tolerated (when the partner cannot offer an API) |
| TLS | 1.3 | Standard or protocol | | Standard |

## 8. Quality requirements

| Attribute | Requirement | Metric |
|---|---|---|
| Availability | The Salesforce Order Platform is available to internal users and to customers at all times, apart from the maintenance windows announced by Salesforce. | 99.9 percent per month |
| Availability | Order capture keeps working when SAP S/4HANA Finance or Reflex WMS is unavailable; messages wait on the queues. | Messages kept for 7 days on Anypoint MQ |
| Performance | A page of the Orvanne Pro Shop loads fast enough for a customer on a mobile network. | 90 percent of pages under 2.5 seconds |
| Performance | An order released in Salesforce reaches the warehouse quickly. | 95 percent of fulfilment orders in Reflex WMS in under 60 seconds |
| Performance | An EDI order is acknowledged quickly. | Order response (ORDRSP) sent in under 15 minutes |
| Scalability | The platform absorbs the autumn peak, when installers prepare the heating season. | 1,900 orders per day, 8,500 order lines per day |
| Reliability | No order and no billing request is lost. | Zero lost message; every failed message is on a dead-letter queue and raises an alert within 5 minutes |
| Reliability | A billing request is never invoiced twice. | SAP ignores a billing request whose identifier it has already processed |
| Security | No card number is stored or processed by Orvanne Group systems. | Scope of the payment card industry standard limited to self-assessment questionnaire A |
| Security | Price agreements are visible only to the sales team of the account and to their managers. | Checked at each release by automated permission tests |
| Compliance | Personal data of contacts is handled in line with the General Data Protection Regulation. | Erasure request executed in under 30 days; inactive leads deleted after 3 years |
| Usability | A sales representative can enter a standard order without training on SAP. | Standard order of 5 lines entered in under 3 minutes |
| Maintainability | Configuration comes before code. | Fewer than 150 Apex classes; test coverage above 85 percent |
| Interoperability | Every integration of the Orvanne Integration Hub is a reusable API described in the API catalogue. | 100 percent of APIs published with an OpenAPI or RAML description |

## 9. Security architecture

**Authentication.** Internal users sign in through single sign-on with Microsoft Entra ID (SAML 2.0), with multi-factor authentication. Customer users of the Orvanne Pro Shop and of the MyOrvanne Portal have their own accounts in Salesforce Experience Cloud, with e-mail verification and optional multi-factor authentication. The Orvanne Integration Hub authenticates to Salesforce with the OAuth 2.0 JWT bearer flow.

**Authorisation.** Access is granted by permission set groups per job (for example *Inside Sales Representative*, *Customer Service Agent*, *Credit Controller*), assigned from Entra ID groups through CRM-15. Account data is shared by sales territory.

**Data protection.** Salesforce Shield encrypts sensitive fields at rest (price agreements, contact telephone numbers, credit data). Event monitoring logs exports and report downloads and sends them to the group's security operations centre. Data is hosted in Salesforce Hyperforce Germany, in line with the principle *Data Resides in the European Union*.

**API security.** Every API of the Orvanne Integration Hub is protected by API Manager policies: OAuth 2.0 client credentials, rate limiting, and IP allow-listing for partners. Queues are encrypted.

## 10. Architecture decisions

| Decision | Date | Rationale |
|---|---|---|
| CRM-AD-01: Manage orders in Salesforce Order Management, not in SAP sales and distribution. | November 2024 | Sales representatives and customer service already worked in Salesforce Sales Cloud and Service Cloud. Keeping the order next to the quote and the case gives one view of the customer, and four sales channels feed one order model. SAP keeps what only it can do: credit, legal invoice, accounting. |
| CRM-AD-02: Check credit in Salesforce from a copy of the SAP credit profile, not by a real-time call to SAP. | January 2025 | A real-time call would stop order capture whenever SAP is in maintenance, which happens every Sunday morning. The copy is refreshed by O2C-02. |
| CRM-AD-03: Use asynchronous queues with dead-letter queues for the exchanges with SAP S/4HANA Finance and Reflex WMS. | January 2025 | The three systems have different maintenance windows. Queues let each system stop without losing messages and without blocking the others. |
| CRM-AD-04: Allow vendor-delivered Salesforce connectors as exceptions to the principle *No Point-to-Point Integration*. | March 2025 | Connectors delivered and maintained by DocuSign, Genesys, Dun & Bradstreet, project44, Adyen and Salesforce itself cost less to run than custom flows on the hub and are upgraded by their vendors. The exception is limited to connectors that exchange data with Salesforce only. |
| CRM-AD-05: Keep prices in Salesforce Revenue Cloud; SAP invoices the price it receives. | February 2025 | Two pricing engines produced different prices on quote and invoice with OrderDesk, the first cause of invoice disputes. |
| CRM-AD-06: Keep Reflex WMS on-premise. | April 2025 | The radio terminals of the warehouse need response times under 300 milliseconds. Reflex WMS was upgraded in 2024 and is the only system for which the principle *SaaS First* was waived. |
| CRM-AD-07: Migrate from OrderDesk in three waves by legal entity and channel rather than in one go. | November 2024 | A single cut-over in the heating season was judged too risky. The price is a transition period with two order systems and the temporary exchanges CRM-14 and O2C-08. |

## 11. Roadmap and projects

| Project | Description | Sponsor | Status | Start | End | Budget (euros) | Systems affected |
|---|---|---|---|---|---|---|---|
| Horizon O2C | Replaces the legacy order entry application OrderDesk with the Salesforce Order Platform and rebuilds the order-to-cash exchanges O2C-01 to O2C-05. Three waves: wave 1, direct sales of Orvanne France SAS (live on 2 February 2026); wave 2, web shop and EDI in France (live on 5 October 2026); wave 3, Orvanne Deutschland GmbH (planned for 1 March 2027). | Sales and Customer Operations | In progress | 6 January 2025 | 31 March 2027 | 4,900,000 | Salesforce Order Platform, SAP S/4HANA Finance, Orvanne Integration Hub, Reflex WMS, OrderDesk |
| OrderDesk Decommissioning | Archives the OrderDesk data in the Orvanne Data Platform and switches off the servers lyo-odk-app-01 and lyo-odk-db-01. | Orvanne Group IT | Planned | 1 April 2027 | 30 June 2027 | 90,000 | OrderDesk, Orvanne Data Platform |
| MyOrvanne Portal Version 2 | Adds delivery tracking, invoice download, online payment of invoices and return requests to the customer portal. | Sales and Customer Operations | Planned | 1 February 2027 | 30 September 2027 | 450,000 | Salesforce Order Platform, project44 Visibility, Adyen Payments |
| Returns Redesign | Lets customers request a return in the portal, prints the return label, and creates the credit memo request automatically at warehouse receipt. | Sales and Customer Operations | Planned | 1 June 2027 | 31 December 2027 | 280,000 | Salesforce Order Platform, Reflex WMS, SAP S/4HANA Finance |
| EDI Customer Onboarding | Connected the 65 EDI customers to the Salesforce Order Platform through Generix EDI Services, replacing the EDI module of OrderDesk. | Sales and Customer Operations | Completed | 2 March 2026 | 5 October 2026 | 310,000 | Generix EDI Services, Salesforce Order Platform, Orvanne Integration Hub |
| Iberia Sales Rollout | Brings the sales teams and customers of Orvanne Iberia SL onto the Salesforce Order Platform, after the Iberia Finance Rollout of the accounting block. | Sales and Customer Operations | On hold | 1 September 2027 | 31 March 2028 | 600,000 | Salesforce Order Platform |

## 12. Risks and open points

1. **OrderDesk runs on unsupported products.** Windows Server 2012 R2, Microsoft SQL Server 2014 and .NET Framework 4.5 no longer receive security fixes, and neither server has a standby. The servers are isolated in the Lyon Internal Server Zone. The risk ends with the OrderDesk Decommissioning project.
2. **Two order systems until wave 3.** Until 1 March 2027 a customer with entities in France and Germany has orders in both the Salesforce Order Platform and OrderDesk. Customer service agents must look in both.
3. **Credit status delay.** The credit profile used by the Credit Check Service can be up to one hour old. The Finance Department has asked for a shorter delay.
4. **Single warehouse.** All fulfilment depends on the Saint-Priest Distribution Centre and on Reflex WMS. The database has a standby, but both are in the same data centre.
5. **Carrier booking is outside the architecture.** Warehouse staff book transport in the Carrier Booking Portals by hand; tracking numbers are typed into Reflex WMS, with an error rate of about 1 percent that breaks CRM-11 for those shipments.
6. **Connector exceptions.** Six satellites are connected outside the Orvanne Integration Hub (decision CRM-AD-04) and are not visible in its monitoring.

## 13. Glossary

| Term | Definition |
|---|---|
| API-led connectivity | The MuleSoft approach that separates experience, process and system APIs. |
| Dead-letter queue | A queue that receives the messages a consumer could not process. |
| EDI | Electronic data interchange: exchange of structured business messages between companies. |
| Fulfilment order | In Salesforce Order Management, the part of an order assigned to one location for one shipment. |
| Hyperforce | Salesforce's infrastructure on public cloud regions, which lets a customer choose where its data resides. |
| O2C | Order to cash: the process from the customer order to the collected payment. |
| Platform event | A message published on the Salesforce event bus. |
| Sandbox | A copy of a Salesforce organisation used for development or tests. |
| Satellite application | An application system that exchanges data with one of the two main blocks. |
| Wave | A go-live step of the Horizon O2C project. |
