"""Publication plots. All numerical positions are derived from core.calculate()."""
from pathlib import Path
import math
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
from analysis.core import calculate, two_sided_normal

BLUE, RED, INK, GREY, BG = "#215BC5", "#BD463D", "#172840", "#617184", "#FAFBFD"


def setup():
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":12,
        "axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,
        "axes.edgecolor":"#BDCAD8","text.color":INK,"axes.labelcolor":GREY,
        "xtick.color":GREY,"ytick.color":GREY,"figure.facecolor":BG,"axes.facecolor":BG,
        "svg.fonttype":"none","savefig.facecolor":BG})


def save(fig,name):
    out=ROOT/"docs"/"assets";out.mkdir(parents=True,exist_ok=True)
    for ext in ["png","svg"]:
        fig.savefig(out/f"{name}.{ext}",dpi=180,bbox_inches="tight",metadata={"Creator":"Mihajlo Popesku / reproducible Python analysis"})
    plt.close(fig)


def generate():
    setup();r=calculate();sns,sl=r["headlines"]
    # Comparison, with the published Ipsos confidence interval.
    fig,ax=plt.subplots(figsize=(12,4.4));fig.subplots_adjust(left=.22,right=.95,top=.72,bottom=.20)
    for y,h in [(1,sns),(0,sl)]:
        ax.plot([h["benchmark_percent"],h["estimate_percent"]],[y,y],color="#C2CBD7",lw=3)
        ax.errorbar(h["estimate_percent"],y,xerr=h["margin_95_pp"],fmt="o",color=RED,capsize=7,lw=2.5,ms=9)
        ax.plot(h["benchmark_percent"],y,"o",color=BLUE,ms=9)
        for x,col,dy in [(h["estimate_percent"],RED,.17),(h["benchmark_percent"],BLUE,-.22)]:
            ax.text(x,y+dy,f"{x:.2f}%".replace(".",","),ha="center",color=col,fontweight="bold")
    ax.set(yticks=[0,1],yticklabels=["Studentska lista","SNS / Ujedinjena Srbija"],xlim=(33,58),ylim=(-.5,1.5),xlabel="Udeo glasova (%) · objavljeni procenti")
    ax.grid(axis="x",color="#DFE5ED",lw=.7);ax.set_axisbelow(True);ax.tick_params(axis="y",length=0)
    fig.suptitle("Procena i referentni rezultat",x=.03,y=.98,ha="left",fontweight="bold",fontsize=22)
    fig.text(.03,.85,"Ipsos: tačka i objavljeni 95% interval     /     RIK: plava tačka",fontsize=13)
    fig.text(.03,.035,"Ipsos, 22.10.2026. · RIK, privremeni presek 30.10.2026. 09:10 · Obuhvat birača se razlikuje.",fontsize=10,color=GREY)
    save(fig,"01-procena-i-rezultat")

    # Normal curve with an affine secondary x-axis and honestly magnified tails.
    fig=plt.figure(figsize=(13,8.3))
    ax=fig.add_axes([.08,.43,.84,.34]);z=sns["abs_z"];se=sns["se_pp"]
    x=np.linspace(-9,9,3000);y=norm.pdf(x)
    ax.plot(x,y,color=BLUE,lw=2.5)
    ax.fill_between(x,y,where=abs(x)<=r["z_975"],color="#DCE8FC",interpolate=True)
    for cut in [-z,z]:
        ax.axvline(cut,color=RED,lw=1.2,ls="--")
    ax.text(0,.105,"95%",ha="center",fontsize=22,fontweight="bold",color=BLUE)
    ax.set(xlim=(-9,9),ylim=(0,.46),yticks=[],xlabel="Odstupanje od RIK-a, u standardnim greškama")
    ticks=[-z,-6,-4,-2,0,2,4,6,z]
    ax.set_xticks(ticks,["−7,87","−6","−4","−2","0","+2","+4","+6","+7,87"])
    top=ax.secondary_xaxis("top",functions=(lambda v:38.97+se*v,lambda p:(p-38.97)/se))
    top.set_xticks([38.97-8.43,38.97,47.4],["Simetrično: 30,54%","RIK: 38,97%","Ipsos: 47,40%"])
    top.tick_params(pad=10,labelsize=12)
    for side,box in [("left",[.12,.13,.32,.16]),("right",[.56,.13,.32,.16])]:
        a=fig.add_axes(box);xx=np.linspace(-9.2,-7.75,700) if side=="left" else np.linspace(7.75,9.2,700)
        yy=norm.pdf(xx)/norm.pdf(7.75)
        a.plot(xx,yy,color=RED,lw=2)
        a.fill_between(xx,yy,where=(xx<=-z if side=="left" else xx>=z),color="#F0BBB5",interpolate=True)
        a.axvline(-z if side=="left" else z,color=RED,lw=1,ls="--")
        a.set(ylim=(0,1.1),yticks=[])
        a.set_xticks([-z] if side=="left" else [z],["−7,87"] if side=="left" else ["+7,87"])
        a.set_title("Levi rep ≈ 1,8 × 10⁻¹⁵" if side=="left" else "Desni rep ≈ 1,8 × 10⁻¹⁵",color=RED,fontsize=12)
    fig.suptitle("Kako se dobija „1 u 280 biliona“?",x=.04,y=.99,ha="left",fontsize=23,fontweight="bold")
    fig.text(.04,.925,"Uslovni normalni model · oba repa zajedno: p ≈ 3,6 × 10⁻¹⁵",fontsize=14,color=RED)
    fig.text(.5,.325,"Repovi su uvećani, na drugoj vertikalnoj skali. Na glavnom grafikonu se praktično ne vide.",ha="center",fontsize=10,color=GREY)
    fig.text(.04,.035,"Važi uz navedene pretpostavke; nije utvrđena verovatnoća greške stvarne ankete niti verovatnoća nameštanja.",fontsize=10,color=GREY)
    save(fig,"02-normalna-dve-ose")

    # Probability comparison: honest logarithmic spacing, no 'two wins somewhere'.
    fig,ax=plt.subplots(figsize=(12,5.1));fig.subplots_adjust(left=.29,right=.83,top=.72,bottom=.24)
    probs=[r["lotto"]["single_p"],r["lotto"]["two_independent_p"],sns["two_sided_p"]]
    labels=["Jedna loto sedmica","Dve loto sedmice","SNS: uslovni normalni model"]
    ends=["1 u 15.380.937","1 u 236,6 biliona","1 u 277,2 biliona"]
    for yy,(pr,col,tx) in enumerate(zip(probs,[BLUE,BLUE,RED],ends)):
        val=-math.log10(pr);ax.hlines(yy,6,val,color="#D3DCE8",lw=2)
        ax.scatter(val,yy,s=110,color=col,zorder=3)
        ax.annotate(tx,(val,yy),xytext=(12,-4),textcoords="offset points",color=col,fontweight="bold",fontsize=11)
    ax.set(xlim=(6,15.3),yticks=range(3),yticklabels=labels,ylim=(2.6,-.6),xlabel="−log₁₀(p) · svaki korak udesno znači 10 puta manju verovatnoću")
    ax.tick_params(axis="y",length=0);ax.grid(axis="x",color="#E2E7EE");ax.set_axisbelow(True)
    fig.suptitle("Približno kao dve loto sedmice",x=.03,y=.98,ha="left",fontsize=23,fontweight="bold")
    fig.text(.03,.855,"Loto 7/39 · jedna kombinacija po izvlačenju · dva unapred određena, nezavisna izvlačenja",fontsize=12)
    fig.text(.03,.05,"Dve sedmice su oko 1,17 puta verovatnije od SNS događaja u izabranom normalnom modelu.\nPoređenje opisuje veličinu brojeva; ne potvrđuje pretpostavke modela ankete.",fontsize=10,color=GREY)
    save(fig,"03-loto-poredjenje")

    fig,ax=plt.subplots(figsize=(12,5.6));fig.subplots_adjust(left=.1,right=.95,top=.76,bottom=.22)
    k=np.linspace(1,4.5,300)
    for h,col,label in [(sns,RED,"SNS"),(sl,BLUE,"Studentska lista")]:
        ax.plot(k,[two_sided_normal(h["abs_z"]/v) for v in k],lw=2.5,color=col,label=label)
    ax.axhline(.05,color=GREY,ls="--",lw=1);ax.text(4.45,.065,"p = 0,05",ha="right",color=GREY)
    ax.set(yscale="log",xlim=(1,4.5),ylim=(1e-35,1),xlabel="Množilac standardne greške (k)",ylabel="Dvostrana verovatnoća p · logaritamska skala")
    ax.grid(color="#E2E7EE",lw=.7);ax.legend(frameon=False,loc="lower right")
    fig.suptitle("Koliko rezultat zavisi od pretpostavljene greške?",x=.03,y=.98,ha="left",fontweight="bold",fontsize=21)
    fig.text(.03,.86,"k = 1: objavljena preciznost  /  k = 2: dvostruka standardna greška, četvorostruka varijansa",fontsize=12)
    fig.text(.03,.04,"Ovo su scenariji osetljivosti, a ne procene stvarne greške Ipsosovog istraživanja.",fontsize=11,color=GREY)
    save(fig,"04-osetljivost")


if __name__=="__main__":
    generate()
