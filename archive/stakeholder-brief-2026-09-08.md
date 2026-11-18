> **Dated 2026-09-08.** Superseded in places by [the current status](README.md#where-things-stand-2026-11-16); kept as written for the record.

# Roadside Biodiversity Monitoring Unit — Status Brief

**Prepared:** 8 September 2026 · **Unit:** bluemar-bio-xnx-2 · **Audience:** project stakeholders

## What the system is

A small computer in a weatherproof box, mounted in a car, with two cameras and a GPS receiver.
While the car drives, it photographs the roadside and automatically recognises two things: **dead
animals** (rear camera) and **seven invasive or indicator plant species** (side camera). A button on
the box lets the driver capture a short 5-second burst of images on demand.

Each photograph is tagged with its GPS position and the species detected, then sent automatically
over the mobile network to a cloud database that can be searched later. Number plates and vehicles
are automatically blurred before anything is stored.

By design the unit only photographs when the car is travelling **above 80 km/h**. This keeps the
survey to open roads and deliberately avoids collecting imagery in towns.

## Where we stand

The unit **works**. Over the last two days we have confirmed the cameras, GPS, the button, the
recording function and the automatic upload to the cloud all operate correctly end to end.

However, the unit was not reliable when we received it, and the reasons are now understood.

## The three problems we found

**1. Loose cabling inside the box.** *(Found and fixed.)*
Two separate cabling faults stopped the unit recording. First, the cameras' network cable had been
moved to the wrong socket, so the computer could not see the cameras at all. Second, the single power
cable that feeds the cameras, the internal network switch **and** the 4G mobile connection was easily
knocked loose — when it was, the unit lost both vision and connectivity at the same moment. Both are
now understood; the fix is a few euros of connector strain relief, and ideally putting the mobile
connection on its own power feed so we retain remote visibility when a camera fault occurs. This
matters because vibration and knocks are normal in a vehicle: as it stands, one loose connector can
silently cost a long stretch of a survey drive.

**2. The unit takes 13 minutes to start.** *(Understood, fix identified.)*
Every time the unit restarts, it spends about thirteen minutes preparing its recognition models
before it can record anything. This should take a few seconds — the software is repeating work it
was supposed to save and re-use, because of a file-permission mistake made when it was built. The
practical effect is that any small hiccup takes the unit out of service for a quarter of an hour, and
that the warning light stays lit during normal start-up, so an operator cannot tell a starting unit
from a broken one. This is a contained software fix.

**3. The unit's warning light is misleading.** *(Understood, fix identified.)*
The yellow light does not mean "camera fault" or "GPS fault" — it means only "the main program has
not reported in for 30 seconds", which is also true during every normal 13-minute start-up. This is
why the light appeared to indicate a permanent fault when the unit was in fact healthy.

None of the three is a design flaw in the concept, and none requires new hardware beyond a cable.

## The significant risk: dependency on the original supplier

The system was built by an external company, **Trifork**, which has discontinued the project. Our
review found that the unit still depends on them in several ways. Two matter to this group:

**All collected imagery is being sent to a cloud account that we do not control.** Every photograph
the unit has ever taken is stored in a Google Cloud project belonging to an organisation outside our
own, along with the searchable database built from it. The unit holds a long-lived access key to that
account. We can see the data; we have no evidence that we own it or control its retention.

**We cannot currently rebuild the software.** A core software component is only available from the
supplier's private repository. We can keep the unit running as it is, and we have identified a way to
recover a copy of that component from the unit itself, but until that is done we cannot repair, change
or reproduce the software for a second unit.

There is also a live remote-access connection from the supplier's network to this unit, which should
be reviewed.

Separately, the access keys for both the supplier's code repository and the cloud storage account are
stored **unprotected** on the unit, readable by any account on the machine. This should be tightened,
and the repository key rotated once we have taken our own copies.

## What we recommend

| Priority | Action | Effort |
|---|---|---|
| **Immediate** | Secure our own copies of the software, models and access credentials from the unit, so the system cannot become unrecoverable. | ~1 day |
| **Immediate** | Establish in writing who owns the cloud project and the collected imagery, and agree either a transfer or a full export. | Legal / commercial |
| **Short term** | Fix the 13-minute start-up and the misleading warning light. | ~2–3 days |
| **Short term** | Replace the internal camera cable and verify stability on a test drive. | ~1 hour |
| **Medium term** | Redirect new uploads to our own cloud storage, so data stops accumulating in an external account. | ~1 day |
| **Medium term** | Replace the supplier's remote-access route with our own. | ~1 day |

## Bottom line

The hardware is sound and the system does what it was built to do. The engineering work needed to
make it dependable is modest and well understood — on the order of one to two weeks.

The real exposure is not technical. It is that our data sits in a discontinued supplier's cloud
account and that we cannot yet rebuild the software independently. Both are fixable, and both get
harder the longer we wait. We recommend authorising the immediate actions now, in parallel with the
technical work.
