"""平时分异常检测、正态化优化和最终分生成算法。"""

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm,shapiro

def build_scores(items,ratio):
 # 空批次直接返回；也避免 numpy 对空数组计算分位数。
 if not items:return []
 ids=np.array([x['student_id'] for x in items]); exams=np.array([x['exam_score'] for x in items],float); regular=np.array([x['original_regular_score'] for x in items],float)
 # 第一步：IQR 与样本 Z-Score 联合识别异常平时分。
 q1,q3=np.percentile(regular,[25,75]); iqr=q3-q1; std=np.std(regular,ddof=1) if len(regular)>1 else 0
 low,high=q1-1.5*iqr,q3+1.5*iqr
 out=np.array([((r<low or r>high) if iqr else False) or (std>0 and abs((r-regular.mean())/std)>3) for r in regular])
 suggested=np.clip(np.where(out,np.clip(regular,low,high) if iqr else regular,regular),0,100)
 # 第二步：按初始综合分的名次生成标准正态分位点。
 ew=float(ratio[0])/10; rw=1-ew; initial=ew*exams+rw*suggested; order=np.argsort(initial); z=norm.ppf((np.arange(1,len(items)+1)-.5)/len(items)); zr=np.empty_like(z); zr[order]=z
 # 第三步：优化 mu、sigma，使反推的平时分改动平方和最小。
 def objective(x): return np.sum(((x[0]+x[1]*zr-ew*exams)/rw-suggested)**2)
 cons=[{'type':'ineq','fun':lambda x:x[1]-0.01},{'type':'ineq','fun':lambda x:(x[0]+x[1]*zr).min()},{'type':'ineq','fun':lambda x:100-(x[0]+x[1]*zr).max()},{'type':'ineq','fun':lambda x:((x[0]+x[1]*zr-ew*exams)/rw).min()},{'type':'ineq','fun':lambda x:100-((x[0]+x[1]*zr-ew*exams)/rw).max()}]
 # SLSQP 支持上下界不等式约束；失败时必须安全回退到 suggested。
 res=minimize(objective,[initial.mean(),max(initial.std(),1)],constraints=cons,method='SLSQP')
 adjusted=np.clip((res.x[0]+res.x[1]*zr-ew*exams)/rw,0,100) if res.success else suggested
 # 仅在 Shapiro-Wilk 支持的样本范围内计算 p 值。
 final=ew*exams+rw*adjusted; p=float(shapiro(final).pvalue) if 3<=len(final)<=5000 else None
 return [{'student_id':int(ids[i]),'exam_score':round(exams[i],1),'original_regular_score':round(regular[i],1),'adjusted_regular_score':round(adjusted[i],1),'final_score':round(final[i],1),'is_regular_outlier':bool(out[i]),'adjust_reason':('检测到异常值并小幅修正' if out[i] else ('为改善正态性小幅修正' if abs(adjusted[i]-regular[i])>=.05 else '无需修正')),'normality_p_value':p} for i in range(len(items))]
