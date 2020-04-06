## WiTPy: An Opensource Toolkit to Analyse Wikipedia Talk Pages

WiTpy is an open-source toolkit that is useful in parsing and analyzing the information present in the talk page of any Wikipedia, we are providing users with comments of users in a tree-like structure stored in JSON format, this library also helps in easy analysis of the extracted data.



### How to use

Below is the small code snippet indicating the usage of this toolkit.

```markdown
import witpy as wp
wp.downlaod("Digital Library")
wp.getAllauthors("Digital Library")
```
