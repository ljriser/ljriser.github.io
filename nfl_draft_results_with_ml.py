# -*- coding: utf-8 -*-
"""NFL_Draft_Results_with_ML.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_0AHL66HQso_6cv4GgNqQ7JnJPBomX41

# Supervised Learning Project: *Learning How Performance at the NFL Combine Impacts NFL Draft Results*

*by* Landon Riser

**Introduction**

This notebook contains work geared towards understanding the relationship between the data collected at the NFL Scouting Combine (Combine) and the subsequent NFL Draft (Draft) results for the years ranging from 1987 through 2021 - specifically attempting to predict how Combine data impacts Draft position, round and whether a player who attended the Combinbe was drafted at all. This dataframe was created by hand by searching the internet for the relevant data and munging disparate sources together to build a dataframe.

For some background on what the data is, the NFL Scouting Combine is a week-long showcase occurring every February where college football players perform physical and mental tests in front of National Football League coaches, general managers, and scouts. These tests are rigorously measured and recorded.

The NFL Draft is an annual event following the Combine where the franchises that make up the NFL select players to join their teams. This work set out to observe how the results of these two events relate and whether any modicum of predictive power can be gained of various aspects of the draft result that might stem from the data collected from the Combine.

**The below code blocks grant access to the CSV file where the data is stored**
"""

# Code to read csv file into Colaboratory:
!pip install -U -q PyDrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
# Authenticate and create the PyDrive client.
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

import warnings
warnings.filterwarnings('ignore')

# 'https://drive.google.com/file/d/1OTqz_A8w4KeBlHvfSm_sS9Ct9shMFv25/view?usp=sharing'
fileDownloaded = drive.CreateFile({'id': '1OTqz_A8w4KeBlHvfSm_sS9Ct9shMFv25'})
fileDownloaded.GetContentFile('nfl_data_combined_2.csv')

"""**We first import all relevant libraries**"""

# Commented out IPython magic to ensure Python compatibility.
import math
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_20newsgroups_vectorized
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, fbeta_score, classification_report
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import  classification_report, confusion_matrix, precision_score, recall_score
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn import ensemble
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_absolute_error
from statsmodels.tools.eval_measures import mse, rmse
from scipy.stats.mstats import winsorize

# %matplotlib inline

nfl_raw = pd.read_csv('nfl_data_combined_2.csv')

import warnings
warnings.filterwarnings('ignore')

nfl_raw.head()

nfl_raw.info()

"""**We will drop the following columns for insufficient data:**

1.   Wonderlic
2.   60Yd Shuttle

"""

nfl_raw.drop(nfl_raw.columns[[8,15]], axis=1, inplace=True)

"""**Looking at distributions to determine how best to handle missing values.**"""

nfl = nfl_raw.copy()

measurements = {1:'Height', 2:'Weight', 3:'Hand Size', 4:'Arm Length', 5:'40_Yard', 6:'Bench Press', 7:'Vert Leap', 8:'Broad Jump', 9:'Shuttle', 10:'3Cone'}

plt.figure(figsize=(24,16))
for key, measurement in measurements.items():
    plt.subplot(4,3,key)
    plt.hist(nfl[measurement])
    plt.title(f"Histogram of {measurement}")
plt.show()

"""Based on the histograms above, we will assign the median of each feature to the missing values since some of the features visibly deviate from normal distribution.

**Using a 'for' loop below to apply the median of the data to each of the pertinent series with missing values.**
"""

columns = ['Hand Size', 'Arm Length', '40_Yard', 'Bench Press', 'Vert Leap', 'Broad Jump', 'Shuttle', '3Cone']
for column in columns:
  nfl[column] = nfl[column].fillna(nfl.groupby('POS')[column].transform('median'))

nfl.info()

"""We've now taken care of missing values for the features of interest.

**For visual inspection of collinearity we display a correlation heatmap with correlation values superimposed.**
"""

plt.figure(figsize=(12,12))
sns.heatmap(nfl_raw.corr(), annot=True, linewidths=2)

"""**Plotting box plots to visualize outliers:**"""

measurements = {1:'Height', 2:'Weight', 3:'Hand Size', 4:'Arm Length', 5:'40_Yard', 6:'Bench Press', 7:'Vert Leap', 8:'Broad Jump', 9:'Shuttle', 10:'3Cone'}

plt.figure(figsize=(24,16))
for key, measurement in measurements.items():
    plt.subplot(4,3,key)
    plt.boxplot(nfl[measurement], whis=2)
    plt.title(f"Box plot of {measurement} (whis=2)")
plt.show()

"""We have seven features with outliers that warrant handling. We'll winsorize the minimum amount required to eliminate all outliers beyond a whisker value of two. Two was chosen instead of the default 1.5 because the data gathered in this set are rigorously measured and thus even outliers could be considered legitimate data."""

winsorize_columns = ['Hand Size', 'Arm Length', '40_Yard', 'Bench Press', 'Broad Jump', 'Shuttle', '3Cone']

for col in winsorize_columns:
  nfl['winsorized_' + col] = winsorize(nfl[col], (0.02, 0.02))

nfl.head()

"""**Winsorized features demonstrate removal of outliers**"""

plt.figure(figsize=(27,15))
for i, col in enumerate(winsorize_columns):
  plt.subplot(4,3,i+1)
  plt.boxplot((nfl['winsorized_' + col]), whis=2)
  plt.title(f"Box plot of {'Winsorized ' + col} (whis=2)")

"""Winsorizing at 0.02 is all it took to eliminate outliers beyond 2 times the IQR.

**Histograms of winsorized features illustrate outlier removal**
"""

plt.figure(figsize=(27,15))
for i, col in enumerate(winsorize_columns):
  plt.subplot(4,3,i+1)
  plt.hist((nfl['winsorized_' + col]))
  plt.title(f"Histogram of {'Winsorized ' + col}")
plt.show()

"""**Now that we've handled the numerical features, we create a new DataFrame with dummy variables for the categorical feature 'POS', which is the position that the player plays and we drop rows with null values which are essentially players who attended the Combine but were not subsequently drafted.**"""

# nfl_drafted DataFrame is used for modeling a binary classification of whether the player was drafted or not
nfl_drafted = nfl.copy()

# Below we are dropping all NaN values and creating dummy values for the various position categories.
nfl_drop = nfl.copy()
nfl_drop.dropna(inplace=True)
position_df = pd.get_dummies(nfl_drop['POS'], drop_first=True)

# Here we are creating a new DataFrame (nfl_pos) by merging the position feature dummy variable DataFrame and the nfl dataframe with the categorical 'POS' feature dropped.
nfl_pos = nfl.drop(['POS'], axis=1).merge(position_df, left_index=True, right_index=True)
nfl_pos.dropna(inplace=True)
nfl_pos.head()

nfl_pos.info()

"""## We are now ready to run models on our cleaned dataset.

**Logistic Regression**
"""

Y = nfl_pos['Round']
X = nfl_pos[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone',
             'CB', 'DB', 'DE', 'DL', 'DT', 'EDG', 'FB', 'FS', 'ILB', 'K', 'LB', 'LS', 'OG', 'OL', 'OLB', 'OT', 'P', 'QB',
             'RB', 'S', 'SS', 'TE', 'WR']]

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, random_state = 123)

lr = LogisticRegression(solver='lbfgs')

lr.fit(X_train, y_train)
lr.score(X_test, y_test)

cross_val_score(lr, X, Y, cv=5)

# First, generate predictions on the test data
nfl_predictions = lr.predict(X_test)
nfl_report = classification_report(y_test, nfl_predictions)
print(nfl_report)

"""Above we ran a logistic regression multiclass classifier model attempting to predict the round in which the player was drafted. 14.6% accuracy is our result, which is not very good. The accuracy scores among the 5 folds are fairly consistent. We'll see if we can improve this by using different models.

**Random Forest Classifier**
"""

nfl_rf_clf = RandomForestClassifier(n_estimators=1000, random_state=123)
nfl_rf_clf.fit(X_train, y_train)
nfl_rf_clf.score(X_test, y_test)

cross_val_score(nfl_rf_clf, X, Y, cv=5)

# First, generate predictions on the test data
nfl_predictions = nfl_rf_clf.predict(X_test)
nfl_report = classification_report(y_test, nfl_predictions)
print(nfl_report)

"""From the Random Forest Classifier model we get an accuracy score of 17%, which is still not good from a business standpoint, but it is a nearly 17% improvement over the logistic regression model. Viewing the classification report above, we observe that the random forest model performs better at predicting players drafted in the first round than any of the other top 7 rounds (which will soon be relevant).

**Linear Regression Model on draft position**
"""

X = sm.add_constant(X)
Y = nfl_pos['draft_position']

results = sm.OLS(Y, X).fit()

results.summary()

"""Running an OLS model to predict draft *position* (as a continuous variable) also does poorly with only 9.2% of the variance explained. This is a difficult dataset for which to achieve high accuracy and predicting a continuous result versus a categorical result naturally will lead to less success.

**We will now focus only on the top 7 rounds for consistency as the modern draft settled on 7 rounds in 1994**
"""

# Here we are eliminating all draft rounds greater than 7
nfl_7 = nfl_pos[(nfl_pos['Round'] <= 7)]

"""**Logistic Regression**"""

Y = nfl_7['Round']
X = nfl_7[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone',
             'CB', 'DB', 'DE', 'DL', 'DT', 'EDG', 'FB', 'FS', 'ILB', 'K', 'LB', 'LS', 'OG', 'OL', 'OLB', 'OT', 'P', 'QB',
             'RB', 'S', 'SS', 'TE', 'WR']]
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, random_state = 123)

lr = LogisticRegression(solver='lbfgs')

lr.fit(X_train, y_train)
lr.score(X_test, y_test)

cross_val_score(lr, X, Y, cv=5)

# First, generate predictions on the test data
nfl_predictions = lr.predict(X_test)
nfl_report = classification_report(y_test, nfl_predictions)
print(nfl_report)

"""The logistic regression model on the top 7 rounds DataFrame improved by almost 2 percentage points or 12% on a relative basis which is a significant improvement by merely filtering out data points that are not represented consistently throughout the data set.

**Random Forest**
"""

nfl_rf_clf = RandomForestClassifier(n_estimators=1000, random_state=123)
nfl_rf_clf.fit(X_train, y_train)
nfl_rf_clf.score(X_test, y_test)

cross_val_score(nfl_rf_clf, X, Y, cv=5)

# First, generate predictions on the test data
nfl_predictions = nfl_rf_clf.predict(X_test)
nfl_report = classification_report(y_test, nfl_predictions)
print(nfl_report)

"""As with the full draft round dataset above, the Random Forest classifier performs better than the Logistic Regression model. After removing the less significant higher rounds (8-10), the random forest model does much better at predicting players drafted in the first round than the subsequent rounds.

**Drafted or Not Drafted?**

We now transition to a less rigorous, binary classification model where we want to predict if a player who attended the NFL combine was drafted or not. We will use the same features as with the prior models, however we will have almost the full dataset at our disposal because before we dropped all rows where the player was not drafted.
"""

nfl_drafted.info()

"""We first must create a new column in the DataFrame of 0s and 1s - 0 representing NOT drafted and 1 representing drafted."""

nfl_drafted['drafted'] = pd.DataFrame(np.where(nfl_raw['draft_position'].isna(), 0, 1))
nfl_drafted.head()

# nfl_drafted.dropna(inplace=True)
nfl_position = pd.get_dummies(nfl['POS'], drop_first=True)

nfl_pos = nfl_drafted.drop(['POS'], axis=1).merge(nfl_position, left_index=True, right_index=True)
nfl_pos.head()

nfl_drafted['drafted'].value_counts(normalize=True)

dummy = DummyClassifier(strategy = 'most_frequent')
dummy.fit(X_train, y_train)
dummy.score(X_test, y_test)
dummy.score(X, Y)

"""Random chance guess would give 58% chance of predicting that the player was drafted and 42% that the player was not drafted.

**We'll now compare a Binary Logistic Regression model to our baseline random chance score**
"""

Y = nfl_drafted['drafted']
X = nfl_drafted[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone']]

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, random_state = 123)

lr = LogisticRegression(solver='lbfgs')

lr.fit(X_train, y_train)
lr.score(X_test, y_test)

"""We get an accuracy score of 63% which is a modest improvement above random chance so the combine data does have some predictive power, though not as much as we'd likely need for it to be impactful in a business sense.

**Confusion Matrices for Visual Appeal**
"""

predictions = lr.predict(X_test)
confusion = confusion_matrix(y_test, predictions, labels=[1, 0])
#print(confusion)

def plot_confusion_matrix(cm,
                          target_names,
                          title='Confusion matrix',
                          cmap=None,
                          normalize=True):
    """
    Given a scikit-learn confusion matrix (CM), make a nice plot.

    Arguments
    ---------
    cm:           Confusion matrix from sklearn.metrics.confusion_matrix

    target_names: Given classification classes, such as [0, 1, 2]
                  The class names, for example, ['high', 'medium', 'low']

    title:        The text to display at the top of the matrix

    cmap:         The gradient of the values displayed from matplotlib.pyplot.cm
                  See http://matplotlib.org/examples/color/colormaps_reference.html
                  `plt.get_cmap('jet')` or `plt.cm.Blues`

    normalize:    If `False`, plot the raw numbers
                  If `True`, plot the proportions

    Usage
    -----
    plot_confusion_matrix(cm           = cm,                  # Confusion matrix created by
                                                              # `sklearn.metrics.confusion_matrix`
                          normalize    = True,                # Show proportions
                          target_names = y_labels_vals,       # List of names of the classes
                          title        = best_estimator_name) # Title of graph

    Citation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """
    import matplotlib.pyplot as plt
    import numpy as np
    import itertools

    accuracy = np.trace(cm) / float(np.sum(cm))
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")


    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label\naccuracy={:0.4f}; misclass={:0.4f}'.format(accuracy, misclass))
    plt.show()

plot_confusion_matrix(cm=confusion, target_names = ['Drafted', 'Not drafted'], title = 'Confusion Matrix',normalize=False)

"""**Attempt at Some Feature Engineering**

We'll attempt to create new variables as the products of the highly correlated features.
"""

nfl_drafted['cone_40_shuttle'] = nfl_drafted.winsorized_40_Yard * nfl_drafted.winsorized_3Cone * nfl_drafted.winsorized_Shuttle
nfl_drafted['height_weight'] = nfl_drafted.Height * nfl_drafted.Weight
nfl_drafted['vert_broad'] = nfl_drafted['Vert Leap'] * nfl_drafted['winsorized_Broad Jump']

Y = nfl_drafted['drafted']
X = nfl_drafted[['height_weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'cone_40_shuttle', 
             'winsorized_Bench Press', 'vert_broad']]

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, random_state = 123)

lr = LogisticRegression(solver='lbfgs')

lr.fit(X_train, y_train)
lr.score(X_test, y_test)

"""We don't observe an improvement from feature reduction by combining products of highly correlated variables.

**Gradient Boost Model**
"""

# Creating training and test sets.
offset = int(X.shape[0] * 0.8)

# Putting 80% of the data in the training set.
X_train, y_train = X[:offset], Y[:offset]

# And putting 20% in the test set.
X_test, y_test = X[offset:], Y[offset:]

# Starting with 500 iterations, using 2-deep trees, and setting the loss function.

params = {'n_estimators': 2000,
          'max_depth': 2,
          'loss': 'deviance'}

# Initializing and fitting the model.
clf = ensemble.GradientBoostingClassifier(**params)
clf.fit(X_train, y_train)

predict_train = clf.predict(X_train)
predict_test = clf.predict(X_test)

def plot_confusion_matrix(cm, classes,normalize,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center", verticalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

import itertools
cm = confusion_matrix(y_test, predict_test)
plot_confusion_matrix(cm,[0,1],False)

cm = confusion_matrix(y_test, predict_test)
plot_confusion_matrix(cm,[0,1],True)

"""Accuracy Score"""

clf.score(X_test, y_test)

"""Precision"""

y_pred = clf.predict(X_test)
precision_score(y_test,y_pred)

"""Recall"""

recall_score(y_test,y_pred)

"""We see from the recall score and from the confusion matrix of the gradient boost model that this model correctly predicts 85% of all observations where the player was drafted and only 40% of the cases where the player was not drafted. Before the gradient boost, we achieved a 63% accuracy score on drafted players from the Logistic Regression - this is encouraging. Additional data could perhaps improve both percentages, but perhaps more easily we could find additional data that might greatly improve the prediction of players not drafted."""

feature_importance = clf.feature_importances_

# Make importances relative to max importance.
feature_importance = 100.0 * (feature_importance / feature_importance.max())
sorted_idx = np.argsort(feature_importance)
pos = np.arange(sorted_idx.shape[0]) + .5
plt.subplot(1,1,1)
plt.barh(pos, feature_importance[sorted_idx], align='center')
plt.yticks(pos, X.columns[sorted_idx])
plt.xlabel('Relative Importance')
plt.title('Variable Importance')
plt.show()

"""**SVC Model**"""

from sklearn.svm import SVC

Y = nfl_drafted['drafted']
X = nfl_drafted[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone']]

# Split the dataset in two equal parts
X_train, X_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.5, random_state=123)

svc_rbf = SVC(kernel='rbf', gamma=0.0001, C=1000)
svc_lin = SVC(kernel='linear', C=10)

svc_rbf.fit(X_train, y_train)
svc_lin.fit(X_train, y_train)

print(f"RBF kernel score: {svc_rbf.score(X_test, y_test)}")
print(f"Linear kernel score: {svc_lin.score(X_test, y_test)}")

"""Above is the SVC model testing for accuracy for the two optimized kernal parameters from the below Grid Search Cross Validation runs. These accuracy numbers achieve the highest values among the binary 'drafted or not drafted' classification models.

**Grid Search Cross Validation I**

Below is a Grid Search CV algorithm for linear and rbf kernels of the SVC model.
"""

# Commented out IPython magic to ensure Python compatibility.
print(__doc__)

# Loading the Digits dataset
digits = datasets.load_digits()

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
n_samples = len(digits.images)
Y = nfl_drafted['drafted']
X = nfl_drafted[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone']]

# Split the dataset in two equal parts
X_train, X_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.5, random_state=123)

# Set the parameters by cross-validation
tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-3, 1e-4],
                     'C': [1, 10, 100, 1000]},
                    {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}]

scores = ['precision', 'recall']
# scores = ['accuracy']
for score in scores:
    print("# Tuning hyper-parameters for %s" % score)
    print()

    clf = GridSearchCV(
        SVC(), tuned_parameters, scoring='%s_macro' % score
    )
    clf.fit(X_train, y_train)

    print("Best parameters set found on development set:")
    print()
    print(clf.best_params_)
    print()
    print("Grid scores on development set:")
    print()
    means = clf.cv_results_['mean_test_score']
    stds = clf.cv_results_['std_test_score']
    for mean, std, params in zip(means, stds, clf.cv_results_['params']):
        print("%0.3f (+/-%0.03f) for %r"
#               % (mean, std * 2, params))
    print()

    print("Detailed classification report:")
    print()
    print("The model is trained on the full development set.")
    print("The scores are computed on the full evaluation set.")
    print()
    y_true, y_pred = y_test, clf.predict(X_test)
    print(classification_report(y_true, y_pred))
    print()

# Note the problem is too easy: the hyperparameter plateau is too flat and the
# output model is the same for precision and recall with ties in quality.

"""The grid search cross validation yielded two different parameter sets for the highest scores for precision and for recall. The difference between the highest and the second highest precision score is significant whereas the values of recall don't differ greatly so the best performing parameter set would be the one yielding the highest precision. Which for the SVC model would be rbf kernel with the largest C value and the smallest gamma value.

**Grid Search Cross validation II**

Below is a Grid Search CV algorithm for the Gradient Boost Classifier
"""

# Commented out IPython magic to ensure Python compatibility.
print(__doc__)

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
Y = nfl_drafted['drafted']
X = nfl_drafted[['Height', 'Weight', 'winsorized_Hand Size', 'winsorized_Arm Length', 'winsorized_40_Yard', 
             'winsorized_Bench Press', 'Vert Leap', 'winsorized_Broad Jump', 'winsorized_Shuttle', 'winsorized_3Cone']]

# Split the dataset in two equal parts
X_train, X_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.5, random_state=123)

# Set the parameters by cross-validation
tuned_parameters = {'n_estimators': [100, 1000, 10000],
          'max_depth': [2, 4, 8],
          'loss': ['deviance', 'exponential']}

scores = ['precision', 'recall']

for score in scores:
    print("# Tuning hyper-parameters for %s" % score)
    print()

    clf = GridSearchCV(
        ensemble.GradientBoostingClassifier(), tuned_parameters, scoring='%s_macro' % score
    )
    clf.fit(X_train, y_train)

    print("Best parameters set found on development set:")
    print()
    print(clf.best_params_)
    print()
    print("Grid scores on development set:")
    print()
    means = clf.cv_results_['mean_test_score']
    stds = clf.cv_results_['std_test_score']
    for mean, std, params in zip(means, stds, clf.cv_results_['params']):
        print("%0.3f (+/-%0.03f) for %r"
#               % (mean, std * 2, params))
    print()

    print("Detailed classification report:")
    print()
    print("The model is trained on the full development set.")
    print("The scores are computed on the full evaluation set.")
    print()
    y_true, y_pred = y_test, clf.predict(X_test)
    print(classification_report(y_true, y_pred))
    print()

# Note the problem is too easy: the hyperparameter plateau is too flat and the
# output model is the same for precision and recall with ties in quality.

"""Conveniently, we achieve the highest precision and the highest recall score for the same parameter set according to our grid search cv algorithm for the above gradient boost model. This also provides the highest accuracy, precision and recall of all the models used for binary classification of whether or not a player was drafted.

# Conclusions

This dataset proved to be poorly predictive of our target variable and there are explanations for that. First, merely measuring physical and mental tests, while helpful for decision makers, are only one factor in the greater scheme of data that determines draft position in the NFL. The one big missing piece to this is productivity and performance on the field in college football, however these elements are more challenging to capture in a dataset such as this. If more time were available to compile this data, I believe a significant improvement could be made in predictive capacity of these models.

The use of GridSearch cross validation on two distinct binary classification models to tune hyperparameters proved helpful in increasing our predictive abilities. The best performing model in aggregate scoring was the Gradient Boost model with a deviance loss function, maximum number of nodes (or max tree depth) of 4 and 100 boosting stages or 'estimators.' Therefore this is the recommended model for this project.
"""