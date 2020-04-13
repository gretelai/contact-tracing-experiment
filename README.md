# Apple + Google Contact Tracing

Rudimenatry implemenation of the Apple + Google [contact tracing specification](https://www.apple.com/covid19/contacttracing)

This simulation runs a series of mock "proximity interactions" between a single subject and a collection of other handsets that 
belong to family, friends, coworkers, and other random people.

At the end, this single subject will report a positive test result, which will trigger all of the other handsets to determine
if they were within proximity to the subject's handset, and if so, at which time intervals.

To run the simulation:

```
pip install -r requirements.txt
python life.py
```

See `report.txt` for an output of other handsets that reported proximities to the subject's handset.

The only information that would be provided to a handset owner is that a) they had proximity to an infected subject and b) the time windows they were within proximity.