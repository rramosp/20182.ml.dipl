from sklearn import datasets
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import sys
import progressbar
from sklearn.neighbors import KNeighborsClassifier
from scipy.stats import multivariate_normal
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import tensorflow as tf
import time

def pbar(**kwargs):
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(.2)
    return progressbar.ProgressBar(**kwargs)

def plot_2D_boundary(predict, mins, maxs, n=200, line_width=3, line_color="black", line_alpha=1, label=None):
    n = 200 if n is None else n
    mins -= np.abs(mins)*.2
    maxs += np.abs(maxs)*.2
    d0 = np.linspace(mins[0], maxs[0],n)
    d1 = np.linspace(mins[1], maxs[1],n)
    gd0,gd1 = np.meshgrid(d0,d1)
    D = np.hstack((gd0.reshape(-1,1), gd1.reshape(-1,1)))
    preds = predict(D)
    levels = np.sort(np.unique(preds))
    levels = [np.min(levels)-1] + [np.mean(levels[i:i+2]) for i in range(len(levels)-1)] + [np.max(levels)+1]
    p = (preds*1.).reshape((n,n))
    plt.contour(gd0,gd1,p, levels=levels, alpha=line_alpha, colors=line_color, linewidths=line_width)
    if label is not None:
        plt.plot([0,0],[0,0], lw=line_width, color=line_color, label=label)
    return np.sum(p==0)*1./n**2, np.sum(p==1)*1./n**2

def plot_2Ddata_with_boundary(predict, X, y, line_width=3, line_alpha=1, line_color="black", dots_alpha=.5, label=None, noticks=False):
    mins,maxs = np.min(X,axis=0), np.max(X,axis=0)    
    plot_2Ddata(X,y,dots_alpha)
    p0, p1 = plot_2D_boundary(predict, mins, maxs, line_width=line_width, 
                line_color=line_color, line_alpha=line_alpha, label=label )
    if noticks:
        plt.xticks([])
        plt.yticks([])
        
    return p0, p1



def plot_2Ddata(X, y, dots_alpha=.5, noticks=False):
    colors = cm.hsv(np.linspace(0, .7, len(np.unique(y))))
    for i, label in enumerate(np.unique(y)):
        plt.scatter(X[y==label][:,0], X[y==label][:,1], color=colors[i], alpha=dots_alpha)
    if noticks:
        plt.xticks([])
        plt.yticks([])


class Example_Bayes2DClassifier():
    
    def __init__ (self, mean0, cov0, mean1, cov1, w0=1, w1=1):
        self.rv0 = multivariate_normal(mean0, cov0)
        self.rv1 = multivariate_normal(mean1, cov1)
        self.w0  = w0
        self.w1  = w1

    def sample (self, n_samples=100):
        n = int(n_samples)
        n0 = int(n*1.*self.w0/(self.w0+self.w1))
        n1 = int(n) - n0
        X = np.vstack((self.rv0.rvs(n0), self.rv1.rvs(n1)))
        y = np.zeros(n)
        y[n0:] = 1
        
        return X,y
        
    def fit(self, X,y):
        pass
    
    def predict(self, X):
        p0 = self.rv0.pdf(X)
        p1 = self.rv1.pdf(X)
        return 1*(p1>p0)
    
    def score(self, X, y):
        return np.sum(self.predict(X)==y)*1./len(y)

    # get limits for numeric computation. 
    # points all along the bounding box should have very low probability
    def get_boundingbox_probs(self, pdf, box_size):
        lp = np.linspace(-box_size,box_size,50)
        cp = np.ones(len(lp))*lp[0]
        bp = np.sum([pdf([x,y]) for x,y in zip(lp, cp)]  + \
                    [pdf([x,y]) for x,y in zip(lp, -cp)] + \
                    [pdf([y,x]) for x,y in zip(lp, cp)]  + \
                    [pdf([y,x]) for x,y in zip(lp, -cp)])
        return bp
    
    def get_prob_mesh(self, xrng, yrng):
        rngs = np.exp(np.arange(15))
        for rng in rngs:
            bp0 = self.get_boundingbox_probs(self.rv0.pdf, rng)
            bp1 = self.get_boundingbox_probs(self.rv1.pdf, rng)
            if bp0<1e-1 and bp1<1e-1:
                break
        print rng
        if rng==rngs[-1]:
            print "warning: bounding box prob size",rng,"has prob",np.max([bp0, bp1])        
        
        rng = 3
        
        # then, compute numerical approximation by building a grid
        mins, maxs = [-rng, -rng], [+rng, +rng]
        n = 100
        d0 = np.linspace(*xrng, num=n)
        d1 = np.linspace(*yrng, num=n)
        gd0,gd1 = np.meshgrid(d0,d1)
        D = np.hstack((gd0.reshape(-1,1), gd1.reshape(-1,1)))

        p1 = np.r_[[self.rv1.pdf(i) for i in D]].reshape(n,n)
        p0 = np.r_[[self.rv0.pdf(i) for i in D]].reshape(n,n)

        return p0,p1
        
    def analytic_score(self):
        """
        returns the analytic score on the knowledge of the probability distributions.
        the computation is a numeric approximation.
        """



        rngs = np.exp(np.arange(15))
        for rng in rngs:
            bp0 = self.get_boundingbox_probs(self.rv0.pdf, rng)
            bp1 = self.get_boundingbox_probs(self.rv1.pdf, rng)
            if bp0<1e-9 and bp1<1e-9:
                break

        if rng==rngs[-1]:
            print "warning: bounding box prob size",rng,"has prob",np.max([bp0, bp1])        
        
        # then, compute numerical approximation by building a grid
        mins, maxs = [-rng, -rng], [+rng, +rng]
        n = 100
        d0 = np.linspace(mins[0], maxs[0],n)
        d1 = np.linspace(mins[1], maxs[1],n)
        gd0,gd1 = np.meshgrid(d0,d1)
        D = np.hstack((gd0.reshape(-1,1), gd1.reshape(-1,1)))

        p1 = np.r_[[self.rv1.pdf(i) for i in D]]
        p0 = np.r_[[self.rv0.pdf(i) for i in D]]

        # grid points where distrib 1 has greater probability than distrib 0
        gx = (p1>p0)*1.

        # true positive and true negative rates
        tnr = np.sum(p0*(1-gx))/np.sum(p0)
        tpr = np.sum(p1*gx)/np.sum(p1)
        return (self.w0*tnr+self.w1*tpr)/(self.w0+self.w1)  

def plot_estimator_border(bayes_classifier, estimator=None, 
                          mins=None, maxs=None,
                          estimator_name=None, n_samples=500,legend=True):    
    estimator_name = estimator.__class__.__name__ if estimator_name is None else estimator_name
    nns = [10,50,100]
    X,y = bayes_classifier.sample(n_samples)
    mins = np.min(X, axis=0) if mins is None else mins
    maxs = np.max(X, axis=0) if maxs is None else maxs
    if estimator is not None:
        estimator.fit(X,y)
        plt.title(estimator_name+", estimator=%.3f"%estimator.score(X,y)+ "\nanalytic=%.3f"%bayes_classifier.analytic_score())
        plot_2D_boundary(estimator.predict, mins, maxs, 
                            line_width=1, line_alpha=.5, label="estimator boundaries")
    else:
        plt.title("analytic=%.3f"%bayes_classifier.analytic_score())
    plot_2Ddata(X, y, dots_alpha=.3)

    plot_2D_boundary(bayes_classifier.predict, mins, maxs, 
                             line_width=4, line_alpha=1., line_color="green", label="bayes boundary")

    plt.xlim(mins[0], maxs[0])
    plt.ylim(mins[1], maxs[1])

    if legend:
         plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

def sample_borders(mc, estimator, samples, n_reps, mins=None, maxs=None):
    plt.figure(figsize=(15,3))
    for i,n_samples in pbar(max_value=len(samples))(enumerate(samples)):
        plt.subplot(1,len(samples),i+1)
        for ii in range(n_reps):
            X,y = mc.sample(n_samples)
            estimator.fit(X,y)
            if ii==0:
                plot_2D_boundary(estimator.predict, np.min(X, axis=0), np.max(X, axis=0), 
                                 line_width=1, line_alpha=.5, label="estimator boundaries")
            else:
                plot_2D_boundary(estimator.predict, np.min(X, axis=0), np.max(X, axis=0), 
                                 line_width=1, line_alpha=.5)                    
            plt.title("n samples="+str(n_samples))
        mins = np.min(X, axis=0) if mins is None else mins
        maxs = np.max(X, axis=0) if maxs is None else maxs
        plot_2D_boundary(mc.predict, mins, maxs, 
                         line_width=5, line_alpha=1., line_color="green", label="bayes boundary")
        plt.xlim(mins[0], maxs[0])
        plt.ylim(mins[1], maxs[1])
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
from sklearn.neighbors import KernelDensity

class KDClassifier:
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        
    def fit(self, X,y):
        """
        builds a kernel density estimator for each class
        """
        self.kdes = {}
        for c in np.unique(y):
            self.kdes[c] = KernelDensity(**self.kwargs)
            self.kdes[c].fit(X[y==c])
        return self
        
    def predict(self, X):
        """
        predicts the class with highest kernel density probability
        """
        classes = self.kdes.keys()
        preds = []
        for i in sorted(classes):
            preds.append(self.kdes[i].score_samples(X))
        preds = np.array(preds).T
        preds = preds.argmax(axis=1)
        preds = np.array([classes[i] for i in preds]) 
        return preds
    
    def score(self, X, y):
    
        return np.mean(y==self.predict(X))
    
    
def accuracy(y,preds):
    return np.mean(y==preds)

    
from sklearn.model_selection import train_test_split
def bootstrapcv(estimator, X,y, test_size, n_reps, score_func=None, score_funcs=None):

    if score_funcs is None and score_func is None:
        raise ValueError("must set score_func or score_funcs")
    
    if score_funcs is not None and score_func is not None:
        raise ValueError("cannot set both score_func and score_funcs")
    
    if score_func is not None:
        rtr, rts = [],[]
    else:
        rtr = {i.__name__:[] for i in score_funcs}
        rts = {i.__name__:[] for i in score_funcs}
        
    for i in range(n_reps):
        Xtr, Xts, ytr, yts = train_test_split(X,y,test_size=test_size)
        estimator.fit(Xtr, ytr)
        if score_func is not None:
            rts.append(score_func(yts, estimator.predict(Xts)))
            rtr.append(score_func(ytr, estimator.predict(Xtr)))
        else:
            for f in score_funcs:
                fname =  f.__name__
                rts[fname].append(f(yts, estimator.predict(Xts)))
                rtr[fname].append(f(ytr, estimator.predict(Xtr)))
    if score_func is not None:
        return np.array(rtr), np.array(rts)
    else:
        rtr = {i: np.array(rtr[i]) for i in rtr.keys()}
        rts = {i: np.array(rts[i]) for i in rts.keys()}
        return rtr, rts

def lcurve(estimator, X,y, n_reps, score_func, show_progress=False):
    test_sizes = np.linspace(.9,.1,9)
    trmeans, trstds, tsmeans, tsstds = [], [], [], []
    for test_size in pbar()(test_sizes):
        rtr, rts = bootstrapcv(estimator,X,y,test_size,n_reps, score_func)
        trmeans.append(np.mean(rtr))
        trstds.append(np.std(rtr))
        tsmeans.append(np.mean(rts))
        tsstds.append(np.std(rts))
    trmeans = np.array(trmeans)
    trstds  = np.array(trstds)
    tsmeans = np.array(tsmeans)
    trstds  = np.array(tsstds)
    abs_train_sizes = len(X)*(1-test_sizes)
    plt.plot(abs_train_sizes, trmeans, marker="o", color="red", label="train")
    plt.fill_between(abs_train_sizes, trmeans-trstds, trmeans+trstds, color="red", alpha=.2)
    plt.plot(abs_train_sizes, tsmeans, marker="o", color="green", label="test")
    plt.fill_between(abs_train_sizes, tsmeans-tsstds, tsmeans+tsstds, color="green", alpha=.2)
    plt.xlim(len(X)*.05, len(X)*.95)
    plt.xticks(abs_train_sizes)
    plt.grid()
    plt.xlabel("train size (%)")
    plt.ylabel(score_func.__name__)
    plt.ylim(0,1)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.25),
              ncol=2, fancybox=True, shadow=True)

def plot_cluster_predictions(clustering, X, n_clusters = None, cmap = plt.cm.plasma,
                             plot_data=True, plot_centers=True, show_metric=False,
                             title_str=""):

    assert not hasattr(clustering, "n_clusters") or \
           (hasattr(clustering, "n_clusters") and n_clusters is not None), "must specify `n_clusters` for "+str(clustering)

    if n_clusters is not None:
        clustering.n_clusters = n_clusters

    y = clustering.fit_predict(X)
    # remove elements tagged as noise (cluster nb<0)
    X = X[y>=0]
    y = y[y>=0]

    if n_clusters is None:
        n_clusters = len(np.unique(y))

    if plot_data:        
        plt.scatter(X[:,0], X[:,1], color=cmap((y*255./(n_clusters-1)).astype(int)), alpha=.5)
    if plot_centers and hasattr(clustering, "cluster_centers_"):
        plt.scatter(clustering.cluster_centers_[:,0], clustering.cluster_centers_[:,1], s=150,  lw=3,
                    facecolor=cmap((np.arange(n_clusters)*255./(n_clusters-1)).astype(int)),
                    edgecolor="black")   

    if show_metric:
        sc = silhouette_score(X, y) if len(np.unique(y))>1 else 0
        plt.title("n_clusters %d, sc=%.3f"%(n_clusters, sc)+title_str)
    else:
        plt.title("n_clusters %d"%n_clusters+title_str)

    plt.axis("off")
    return

def experiment_number_of_clusters(X, clustering, show_metric=True,
                                  plot_data=True, plot_centers=True, plot_boundaries=False):
    plt.figure(figsize=(15,6))
    for n_clusters in pbar()(range(2,10)):
        clustering.n_clusters = n_clusters
        y = clustering.fit_predict(X)

        cm = plt.cm.plasma
        plt.subplot(2,4,n_clusters-1)

        plot_cluster_predictions(clustering, X, n_clusters, cm, 
                                 plot_data, plot_centers, show_metric)


def experiment_KMeans_number_of_iterations(X, n_clusters=3,
                                    plot_data=True, plot_centers=True, plot_boundaries=False):
    plt.figure(figsize=(15,6))
    for i in pbar()(range(10)):
        init_centroids = np.vstack((np.linspace(np.min(X[:,0]), np.max(X[:,0])/20, n_clusters), 
                                    [np.min(X[:,1])]*n_clusters)).T

        x0min, x0max = np.min(X[:,0]), np.max(X[:,0])
        x1min, x1max = np.min(X[:,1]), np.max(X[:,1])
        c = np.random.random(size=(n_clusters, 2))/3
        c[:,0] = x0min + c[:,0]*(x0max-x0min)
        c[:,1] = x1min + c[:,1]*(x1max-x1min)
        init_centroids = c

        plt.subplot(2,5,i+1)
        cm = plt.cm.plasma
        
        if i==0:
            
            y = np.argmin(np.vstack([np.sqrt(np.sum((X-i)**2, axis=1)) for i in init_centroids]).T, axis=1)
            
            plt.scatter(X[:,0], X[:,1], color=cm((y*255./(n_clusters-1)).astype(int)), alpha=.5)
            plt.scatter(init_centroids[:,0], init_centroids[:,1], s=150,  lw=3,
                       facecolor=cm((np.arange(n_clusters)*255./(n_clusters-1)).astype(int)),
                       edgecolor="black")   
            plt.axis("off")
            plt.title("initial state")
            

        else:
            n_iterations = i if i<4 else (i-1)*2

            km = KMeans(n_clusters=n_clusters, init=init_centroids, n_init=1, max_iter=2*n_iterations)
            km.fit(X)

            plot_cluster_predictions(km, X, n_clusters, cm, plot_data, plot_centers, plot_boundaries)

            plt.title("n_iters %d"%(n_iterations))


def optimize(optimizer, loss, accuracy, params, test_mode):


    train_hist = []
    test_hist  = []

    with tf.Session() as sess:

        tf.global_variables_initializer().run()
        tf.tables_initializer().run()
        i=0
        while True:
            try:
                _, nloss,naccuracy = sess.run([optimizer, loss, accuracy])
                train_hist.append([nloss, naccuracy])
                if i%30==0:
                    test_nloss, test_naccuracy = sess.run([loss, accuracy], feed_dict={test_mode: True})
                    test_hist.append([test_nloss, test_naccuracy])
                    print "\rstep %10d  train_acc %.2f test_acc %.2f"%(i,naccuracy, test_naccuracy),
                i+=1
            except tf.errors.OutOfRangeError as e:
                print "\nfinished iteration"
                break
        nparams = sess.run([params])
        train_hist, test_hist = np.r_[train_hist], np.r_[test_hist]
    return train_hist, test_hist, nparams

def logreg_model(train_input_fn, test_input_fn=None):
        
    test_input_fn = test_input_fn if test_input_fn is not None else train_input_fn
    
    # find out input size
    tf.reset_default_graph()
    nx,_ = test_input_fn()
    with tf.Session() as sess:
        tf.tables_initializer().run()
        tf.global_variables_initializer().run()
        input_size = sess.run(nx).shape[1]    
    
    # now build the graph
    tf.reset_default_graph()
    train_nX, train_ny = train_input_fn()
    test_nX,  test_ny  = test_input_fn()

    test_mode = tf.Variable(initial_value=False, name="test_mode", dtype=tf.bool)
    next_X, next_y = tf.cond(test_mode, lambda: (test_nX, test_ny),
                                        lambda: (train_nX, train_ny)) 

    t = tf.Variable(initial_value=tf.random_uniform([input_size,1]), name="t", dtype=tf.float32)
    b = tf.Variable(initial_value=tf.random_uniform([1]), name="b", dtype=tf.float32)

    y_hat      = tf.sigmoid(b+tf.matmul(next_X,t))*.9+.05
    prediction = tf.reshape(tf.cast(y_hat>.5, tf.float32), (-1,1))
    accuracy   = tf.reduce_mean(tf.cast(tf.equal(prediction,next_y), tf.float32))
    
    loss = -tf.reduce_mean(next_y*tf.log(y_hat)+(1-next_y)*tf.log(1-y_hat))

    return y_hat, prediction, accuracy, loss, [t,b], test_mode



def plot_hists(train_hist, test_hist):

    plt.figure(figsize=(10,3))
    plt.subplot(121)
    plt.title("train loss")
    plt.grid()
    plt.plot(train_hist[:,0])
    plt.subplot(122)
    plt.plot(train_hist[:,1])
    plt.title("train accuracy")
    plt.grid()

    plt.figure(figsize=(10,3))
    plt.subplot(121)
    plt.title("test loss")
    plt.plot(test_hist[:,0])
    plt.grid()
    plt.subplot(122)
    plt.plot(test_hist[:,1])
    plt.title("test accuracy")
    plt.grid();
