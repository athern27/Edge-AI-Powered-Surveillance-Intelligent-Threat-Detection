## Steps on how to use this
1. Create dataset on Roboflow.
2. Auto-Annotate it.
3. Download as Pascal Voc.
4. Pascal VOC gives you in this format
   
``` bash
├───train --It contains both xml and images in one folder
└───valid --It contains both xml and images in one folder
```

5. But we need It in this form 
``` bash
├───xml
└───images
└───labels.txt --It contains labels
```

6. To do this Run CreateDataset file.

