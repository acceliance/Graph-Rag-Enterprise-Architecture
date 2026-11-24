# Sample architecture documents

Two architecture documents of a **fictive enterprise, Orvanne Group**, written as test data for the Graph RAG enterprise architecture agent, and the agent profile used to question them.

Orvanne Group, its people, its figures and its integrator partners are invented. The software products it uses (SAP S/4HANA, Salesforce, MuleSoft, Esker, Kyriba and others) are real products, named only to make the landscape realistic; nothing here describes how any real company uses them.

| Folder | Content |
|---|---|
| [`source-docs/`](source-docs/) | The 2 PDFs described below, to upload on the *Documents* screen |
| [`src/`](src/) | The Markdown sources of the PDFs and the script that builds them |
| [`profiles/`](profiles/) | [`enterprise-architect.md`](profiles/enterprise-architect.md), the *Enterprise Architect* agent profile that infers the landscape from these documents through [the model](../model/enterprise-architecture-model.json); import it from *Admin ▸ Profiles* |

## The enterprise

Orvanne Group is a business-to-business distributor of heating, ventilation and air-conditioning equipment, based in Lyon, with entities in France, Germany and Spain. Its information system has two main blocks:

| Block | System | Role |
|---|---|---|
| Accounting | **SAP S/4HANA Finance** (RISE private cloud on Azure) | General ledger, payables, receivables, credit management, legal invoices, inventory valuation |
| Order management | **Salesforce Order Platform** (Sales Cloud, Revenue Cloud, Order Management, Service Cloud, B2B Commerce) | Customer accounts, quotes, orders of four sales channels, fulfilment orchestration, customer service |

Around them are about 25 satellite applications (invoice platform, treasury, expenses, close, payroll, warehouse management, product information, EDI, payment provider, data platform, archive, two legacy applications…) and three integration platforms.

## Documents

| # | File | Title | Reference | Version | Date | Pages |
|---|---|---|---|---|---|---|
| 01 | `01_Architecture_SAP-S4HANA-Finance_Orvanne.pdf` | SAP S/4HANA Finance Architecture Document | ORV-ARC-FIN-001 | 2.3 | 12 Oct 2026 | 17 |
| 02 | `02_Architecture_Salesforce-Order-Platform_Orvanne.pdf` | Salesforce Order Platform Architecture Document | ORV-ARC-O2C-002 | 1.6 | 26 Oct 2026 | 17 |

Both documents are in English and follow the same plan, so that every class of [the model](../model/README.md) has something to extract:

| Section | Content | Model classes |
|---|---|---|
| Document control | Reference, version, authors, approvers, revision history | `ArchitectureDocument`, `DocumentRevision`, `Person` |
| 2. Enterprise context | Organisations involved, the group's architecture principles | `Organisation`, `ArchitecturePrinciple` |
| 3. Business architecture | Business capabilities with current and target maturity | `BusinessArea`, `BusinessCapability` |
| 4. Application architecture | The block and its components, **the satellite applications** (context diagram and table), integration platforms, data ownership | `ApplicationSystem`, `Component`, `DataObject` |
| 5. Data exchanges | **Catalogue of exchanges** (source, target, mechanism, protocol, format, frequency, volume), a description of each, field-level record layouts | `DataExchange`, `DataElement` |
| 6. Infrastructure | Sites, network zones, nodes with sizing, environments | `Site`, `NetworkZone`, `InfrastructureNode` |
| 7. Technology standards | Products and protocols with version and status | `Technology` |
| 8–10. Quality, security, decisions | Quality requirements with metrics, architecture decisions with rationale | `QualityRequirement`, `ArchitectureDecision` |
| 11–12. Roadmap, risks | Projects with dates, budget and affected systems; risks | `Project` |

### Exchange numbering

| Prefix | Meaning | Count | Described in |
|---|---|---|---|
| `O2C` | Order to cash: exchanges that cross the two blocks | 8 | Both documents, each from its own side |
| `FIN` | Exchanges of the accounting block only | 16 | Document 01 |
| `CRM` | Exchanges of the order management block only | 15 | Document 02 |

## What the pair is built to test

- **Shared entities.** The two documents name the same systems (Orvanne Integration Hub, Reflex WMS, Akeneo PIM, MFT Gateway…), sites, nodes, people, principles and the *Horizon O2C* project with identical names, and the eight `O2C` exchanges appear in both. Entity resolution should give one node for each.
- **One planted contradiction.** `O2C-02 Customer Credit Status` runs *every 15 minutes* according to document 01 (issued by the source side) and *every hour* according to document 02. Every other attribute of the shared exchanges is identical. The agent should report both values, not pick one.
- **Stubs.** Some systems are referenced but deliberately not described: *Orvanne HR Core* and *Public Invoicing Portal* (document 01), *Carrier Booking Portals* (document 02), *House Bank EBICS Servers*.
- **Legacy and transition.** *Sage X3 Iberia* (legacy) and *OrderDesk* (decommissioning) come with the projects that replace them and the temporary exchanges that disappear with them (`FIN-11`, `O2C-08`, `CRM-14`).
- **Principle exceptions.** A manual exchange (`FIN-11`) and vendor connectors (decision CRM-AD-04) break *No Point-to-Point Integration*; the documents say so.
- **Multi-hop questions.** For example: which systems stop if the Lyon Vénissieux Data Centre is lost; or the path of a web shop order from payment authorisation (`CRM-07`) to cleared invoice (`O2C-06`).

The [*Enterprise Architect* profile](profiles/enterprise-architect.md) turns these points into agent behaviour and lists questions to try, layer by layer.

## Rebuilding the PDFs

The PDFs are generated from the Markdown files of [`src/`](src/); edit those, never the PDFs.

```bash
python samples/src/build.py
```

The script needs [pandoc](https://pandoc.org/) on the PATH and Microsoft Edge or Google Chrome (used headless to print the PDF). It draws the context diagram of each document from its `context` block, and writes one PDF per Markdown file into `source-docs/`.

## Rights and usage

The documents were written for this repository and are covered by its [licence](../LICENSE). Product and company names of software vendors are trademarks of their owners.
