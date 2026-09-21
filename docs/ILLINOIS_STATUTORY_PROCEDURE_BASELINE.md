# Illinois Statutory Procedure Baseline for Civic Profiles

## Status

Architecture/source baseline. Documentation only.

This document records a design rule: where Illinois law already defines a procedural relationship, notice method, record duty, member right, or institutional role, a Civic Infrastructure profile should reuse and cite that statutory source rather than invent a competing civic procedure.

This does **not** mean Kane Fabric itself becomes a condominium association, school district, government agency, or other statutory institution. The statute governs the underlying institution where applicable; Kane Fabric uses the statute as authoritative vocabulary and procedure evidence for its diagnostic profile.

## Initial source: Illinois Condominium Property Act

Primary Illinois source:

`765 ILCS 605` — Condominium Property Act.

Current official Illinois General Assembly text was reviewed on 2026-09-21 for Sections 18, 18.4, 18.8, and 19.

These sections already supply important procedural primitives for the HOA Diagnostics profile.

## Member and board role separation

Section 18 requires bylaws to provide for election of a board of managers from among unit owners and establishes detailed voting/meeting rules.

Section 18.4 states that the board exercises association powers except powers reserved by law to the members.

Design implication:

Kane Fabric should preserve statutory role distinctions instead of flattening `unit owner`, `member`, `board member`, and service-provider roles into one HOA identity.

## Open proceedings and participant observation

Section 18 provides that board meetings are generally open to unit owners, subject to specified closed-session exceptions.

It also gives unit owners the right to record open board proceedings, subject to reasonable rules.

Design implication:

HOA Diagnostics already has statutory precedent for participant observation, recording, and later comparison of institutional conduct. Civic scrubbing should cite the statutory right where the underlying event falls within it rather than describing observation as a new operator-created privilege.

## Notice and delivery

Section 18 establishes notice requirements for board meetings, including physical posting and, where applicable, notice by technological means, mail, or delivery.

Section 18.8 allows notices, signatures, votes, consents, and approvals required under the Act or condominium instruments to use acceptable technological means.

Section 18.8 also preserves a non-technological path when a person has not provided written authorization to conduct business using acceptable technological means.

Section 18.4 allows unit owners to designate an electronic address, U.S. Postal Service address, or both for specified association lists/communications.

Design implication:

Postal and electronic delivery are already first-class statutory mechanisms. Civic Infrastructure should record the actual delivery/notice method and statutory context rather than treating portal delivery as inherently authoritative.

## Durable electronic evidence

Section 18.8 permits electronic voting, consent, and approval when a record is created as evidence and maintained for as long as the corresponding nonelectronic record would be required.

Design implication:

The Civic Infrastructure preference for durable provenance and inspectable records is compatible with the statutory model. The important property is not 'digital' by itself; it is creation and retention of an evidentiary record.

## Association records and inspection

Section 19 requires the association to keep specified records, including governing instruments, contracts, member information, ballots/proxies, financial books and records, and reserve studies.

For major categories of association records, a member may submit a written request identifying the records sought. Failure to make requested records available within 10 business days is deemed a denial under the section.

Section 19 also distinguishes records subject to different access conditions and identifies categories that need not be disclosed absent other authority.

Design implication:

Peer scrubbing must respect the difference between:

- facts/records participants are legally entitled to inspect;
- participant-held first-hand evidence;
- public records;
- private or statutorily restricted records.

Scrubbing is not a justification for publishing material the participant has no right to disclose.

## Fiduciary and accurate-record duties

Section 18.4 requires detailed, accurate records of receipts and expenditures affecting the property and states that board officers and members must exercise the care required of a fiduciary of the unit owners.

Design implication:

HOA Diagnostics can compare observed conduct and records against duties that already exist in Illinois law. Kane Fabric does not need to invent a parallel ethical standard for the Board.

## Mail and physical-delivery precedent

Section 18 contains procedures in which ballots may be distributed and returned by mail or other authorized delivery methods.

This does not make the Civic SASE procedure a statutory condominium procedure.

It does demonstrate that Illinois condominium governance already recognizes physical mail/delivery as a legitimate procedural mechanism with evidentiary consequences.

## Statutory source versus Civic addition

### Reused statutory primitives

Depending on the profile and fact pattern, these may come directly from Illinois law:

- institutional/member roles;
- notice requirements;
- delivery methods;
- open-meeting rights;
- recording rights;
- voting/election procedures;
- record-maintenance duties;
- inspection/request rights;
- response deadlines;
- fiduciary duties;
- statutory limitations/exceptions.

### Civic Infrastructure additions

These are not claimed here to be created by the Condominium Property Act:

- six-month SASE participation renewal for Kane Fabric;
- any active participant becoming a Civic SASE validator/operator;
- Civic Issuance Records;
- participant-maintained affordance claims;
- Same-and-Equal policy machinery;
- peer scrubbing/confirmation/challenge records;
- ESP32-S3 appliance issuance;
- future Witness Attestation.

Those are Civic Infrastructure mechanisms that may reference statutory facts and procedures.

## Profile-specific statutory mapping

The HOA Diagnostics profile should map each relationship/procedure to the statute actually governing the underlying institution.

For Illinois condominium associations, the Condominium Property Act is a primary source.

Other HOA forms may instead or additionally implicate the Common Interest Community Association Act or other law.

School, taxing-district, public-records, court-linked, and other civic profiles must use their own applicable Illinois statutory sources rather than importing condominium procedures by analogy.

## Architecture rule

Before designing a Civic workflow for a profile:

1. identify the underlying Illinois institution/relationship;
2. identify the controlling or relevant statute(s);
3. extract the statutory roles, records, notices, deadlines, delivery methods, and rights;
4. encode those as source-linked policy vocabulary;
5. add only the Civic Infrastructure mechanisms that the statute does not supply;
6. never represent a Civic-added procedure as though Illinois law required it.

## Current HOA baseline

For the first HOA Diagnostics consumer, the immediate statutory anchors are:

- `765 ILCS 605/18` — bylaws, elections, meetings, notice, recording and related unit-owner procedures;
- `765 ILCS 605/18.4` — board powers/duties, records, rules, addresses, fiduciary duty;
- `765 ILCS 605/18.8` — acceptable technological means and evidence-retention rule;
- `765 ILCS 605/19` — association records and member inspection rights.

Future profile work should expand the source map only as needed by the specific affordance or diagnostic surface being defined.
