# .vidx File Format

## v1.0

### A zip file with the .vidx extension, with a master XML file, and for each frame a pair of XML and GIF files.

* Each XML file describes the time taken per frame in ms, any subtitle, and the GUID (filename without .gif) of the associated frame .gif present in the archive.

* A single XML file describes basic file metadata, and has the guaranteed-not-to-be-globally-unique GUID of {6265616e-6f67-616d-6572-206265616e6f}.

* Each XML frame file is named with a sequentially numbered non-globally unique GUID. It will reference a .gif, with a random non-globally unique GUID as a name.

Example file XML (`{6265616e-6f67-616d-6572-206265616e6f}.xml`):

```xml
<?xml version="1.0"?>
<video>
  <version>11</version>
  <width>960</width>
  <height>960</height>
  <frames>15</frames>
</video>
```

Example frame XML (e.g. `{00000000-0000-0000-0000-000000000000}.xml`, first frame of video):

```xml
<?xml version="1.0"?>
<frame>
  <meta>
    <subtitle></subtitle>
  </meta>
  <frame-info>
    <duration>500</duration>
    <data-guid>{29d1d4e6-7498-4474-8ad1-bd0c88b4e329}</data-guid> <!-- First frame is {29d1d4e6-7498-4474-8ad1-bd0c88b4e329}.gif -->
  </frame-info>
</frame>
```
