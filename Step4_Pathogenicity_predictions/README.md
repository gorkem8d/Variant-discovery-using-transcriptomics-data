## Pathogenicity Prediction Scoring Tools
There is two approaches to score the pathogenicity of variants from variant effect predictor output.
# Manual scoring method:
This method incorporates multiple variant characteristics to calculate a comprehensive score for each variant. The scoring system begins with a base score assignment based on predicted variant consequences, ranging from 1 to 20. High impact variants such as frameshift mutations and stop gained variants receive the maximum score of 20, while moderate impact variants like missense mutations are assigned scores between 10-15. Low impact variants including synonymous changes receive scores of 3-5, and modifier variants such as intergenic changes receive the minimum score of 1. The base score is then modified by additional criteria, with each qualifying characteristic adding 10 points to the variant's score.

# ML-based scoring method:
The second approach implements an unsupervised machine learning algorithm to score and rank variants that integrates multiple lines of evidence and effectively handles missing prediction data. ML scoring method works like a detective to find suspicious variants. This approach is more refined since we are looking for unusual variants that might be missed by standard approaches.

-Feature extraction, there are multiple characteristics to evaluate.

-Track missing data, mark which characteristics are missing

-Anomaly detection – subtle one

	-Isolation forest: divides the crowd randomly, the ones isolated quickly is an anomaly.
 
	-Local outlier factor: Compares the density deviation of a point from its neighbors. Points with lower density than their neighbors are considered outliers or anomalies
 
-Combine anomaly scores: 

	-Another level of anomaly detection is PCA distance scores, catches the extremes, simpler (to catch variants without clear pathogenic behavior but may be potentially important)
 
	-The scores are combined with adaptive weights based on variant characteristics
 
-Score transformation:

	-Adaptive sigmoid function, steepness lower when there is missing values. expresses reduced statistical confidence when data is missing.
 
	-Boosts for specific cases, such as rare variants with high impact. 
 
-Missing data post-processing
	-Boosting what is available to compansate the missing data. 
	To counteract the systemic bias because variants with missing prediction data often receive lower initial scores
 	(Eg. No prediction data but only present in SLE patients) 
In the end we have the output, a score for each variant.





 
