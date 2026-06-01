import pandas as pd
from pathlib import Path
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def basicColHist(df, 
                 var: str, 
                 df2: str|None =None,
                 df1Name: str = 'df1', 
                 df2Name: str = 'df2', 
                 title: str | None = None, 
                 xLabel: str | None = None, 
                 saveFig: bool = False, 
                 savePath: Path = Path(),
                 df_name: str = 'default',
                 dfComp:bool =False,
                 ) -> None:
    
    if dfComp == True:
    
        fig, (ax1, ax2) = plt.subplots(1,2, figsize=(8,5))
        
        sns.histplot(df[var], bins=50, ax=ax1)
        sns.histplot(df2[var], bins=50, ax=ax2)

        
        if title is None:
            title = f'{var} of BH-Sol systems at S1 SN'
        if xLabel is None:
            xLabel = var

        ax1.set_title(df1Name)
        ax2.set_title(df2Name)

        ax1.set_xlabel(xLabel)
        ax2.set_xlabel(xLabel)

        ax1.set_ylabel('Count')

        plt.suptitle(title)
        plt.tight_layout()
    else:
        fig, ax = plt.subplots(figsize=(8,5))
        
        sns.histplot(df[var], bins=50, ax=ax)
        
        if title is None:
            title = f'{var} of BH-Sol systems at S1 SN'
        if xLabel is None:
            xLabel = var

        ax.set_title(title)
        ax.set_xlabel(xLabel)
        ax.set_ylabel('Count')

    if saveFig:
        clean_name = title.replace(' ', '_').replace('/', '-') + '.pgf'
        plt.savefig(savePath / clean_name, bbox_inches='tight')

    plt.show()

def genVarHist(var: list, 
               title: str | None = None, 
               xLabel: str | None = None, 
               saveFig: bool = False, 
               savePath: Path = Path()) -> None:
    
    fig, ax = plt.subplots(figsize=(8,5))
    
    sns.histplot(var, bins=50, ax=ax)
    
    if title is None:
        title = 'default'
    if xLabel is None:
        xLabel = 'default'

    ax.set_title(title)
    ax.set_xlabel(xLabel)
    ax.set_ylabel('Count')

    if saveFig:
        clean_name = title.replace(' ', '_').replace('/', '-') + '.pgf'
        plt.savefig(savePath / clean_name, bbox_inches='tight')

    plt.show()

def xVsY(
    xvar: str|list, yvar: str|list,
    df: pd.DataFrame | None = None,
    df2: pd.DataFrame | None = None,
    useDF: bool = True, 
    title: str | None = None,
    df1_Name: str | None = 'df1',
    df2_Name: str | None = 'df2',
    xLabel: str | None = None,
    yLabel: str | None = None,
    saveFig: bool = False,
    savePath: Path = Path(),
    fit: bool = False,
    ci: int = 95,
    df_name: str = 'default',
    df_comp: bool = False,
    xlog:bool = False,
    ylog:bool = False

    ) -> None:
    
    if df_comp == True:
        fig, (ax1, ax2) = plt.subplots(1,2, figsize=(8, 5))
        x1, y1, = df[xvar] ,df[yvar]
        x2, y2, = df2[xvar],df2[yvar]

        if fit:
            sns.regplot(x=x1, y=y1, ci=ci, ax=ax1,
                    line_kws={"color": "red", "linestyle": "--", "linewidth": 2},
                    scatter_kws={"alpha": 0.6})
            sns.regplot(x=x2, y=y2, ci=ci, ax=ax2,
                    line_kws={"color": "red", "linestyle": "--", "linewidth": 2},
                    scatter_kws={"alpha": 0.6})
        else:
            sns.scatterplot(x=x1, y=y1, alpha=0.6, ax=ax1)
            sns.scatterplot(x=x2, y=y2, alpha=0.6, ax=ax2)

        if title is None:
            if isinstance(xvar, str) and isinstance(yvar, str):
                title = f'{xvar} vs {yvar} of BH-Sol systems at S1 SN'
            else:
                title = 'Variable Comparison'

        if xLabel is None:
            xLabel = xvar if isinstance(xvar, str) else 'X-Axis'
            
        if yLabel is None:
            yLabel = yvar if isinstance(yvar, str) else 'Y-Axis'

        ax1.set_title(df1_Name)
        ax2.set_title(df2_Name)
        plt.suptitle(title)
        ax1.set_xlabel(xLabel)
        ax2.set_xlabel(xLabel)
        ax1.set_ylabel(yLabel)

    
    else:
        fig, ax = plt.subplots(figsize=(8, 5))
        if useDF:
            x = df[xvar] if isinstance(xvar, str) else xvar
            y = df[yvar] if isinstance(yvar, str) else yvar
        else:
            x, y = xvar, yvar  
            
        if fit:
            sns.regplot(x=x, y=y, ci=ci, ax=ax,
                        line_kws={"color": "red", "linestyle": "--", "linewidth": 2},
                        scatter_kws={"alpha": 0.6})
        else:
            sns.scatterplot(x=x, y=y, alpha=0.6, ax=ax)

        if title is None:
            if isinstance(xvar, str) and isinstance(yvar, str):
                title = f'{xvar} vs {yvar} of BH-Sol systems at S1 SN'
            else:
                title = 'Variable Comparison'

        if xLabel is None:
            xLabel = xvar if isinstance(xvar, str) else 'X-Axis'
            
        if yLabel is None:
            yLabel = yvar if isinstance(yvar, str) else 'Y-Axis'

        ax.set_title(title)
        ax.set_xlabel(xLabel)
        ax.set_ylabel(yLabel)

    if xlog == True:
        plt.xscale('log')

    if ylog == True:
        plt.yscale('log')

    if saveFig:
        clean_name = title.replace(' ', '_').replace('/', '-') + '.pgf'
        plt.savefig(savePath / clean_name, bbox_inches='tight')

    plt.show()