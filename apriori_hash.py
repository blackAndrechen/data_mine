#-*- coding: utf-8 -*-
import os
import time
from tqdm import tqdm

def load_data(path):#根据路径加载数据集
    ans=[]#将数据保存到该数组
    if path.split(".")[-1]=="xls":#若路径为药方.xls                    
        from xlrd import open_workbook
        import xlwt
        workbook=open_workbook(path)
        sheet=workbook.sheet_by_index(0)#读取第一个sheet
        for i in range(1,sheet.nrows):#忽视header,从第二行开始读数据,第一列为处方ID,第二列为药品清单
            temp=sheet.row_values(i)[1].split(";")[:-1]#取该行数据的第二列并以“;”分割为数组
            if len(temp)==0: continue
            temp=[j.split(":")[0] for j in temp]#将药品后跟着的药品用量去掉
            temp=list(set(temp))#去重，排序
            temp.sort()
            ans.append(temp)#将处理好的数据添加到数组
    elif path.split(".")[-1]=="csv":
        import csv
        with open(path,"r") as f:
            reader=csv.reader(f)
            for row in reader:
                row=list(set(row))#去重，排序
                row.sort()
                ans.append(row)#将添加好的数据添加到数组
    return ans#返回处理好的数据集，为二维数组

def save_rule(rule,path):#保存结果到txt文件
    with open(path,"w") as f:
        f.write("index  confidence"+"   rules\n")
        index=1
        for item in rule:
            s=" {:<4d}  {:.3f}        {}=>{}\n".format(index,item[2],str(list(item[0])),str(list(item[1])))
            index+=1
            f.write(s)
        f.close()
    print("result saved,path is:{}".format(path))

class Apriori_hash():
    ##散列技术在此实现
    ##基于散列技术一次遍历数据，即可生成l1，l2，l3
    ##不生成l4是因为迭代生成候选项时导致可能性太多，数据量大时占用内存太大
    def create_l1_l3(self,data_set,support_data,min_support):#基于散列技术一次遍历数据集生成L1,L2,L3
        L=[set() for i in range(3)]#用于保存频繁项
        item_count={}
        for i in tqdm(data_set):#一次遍历数据集
            l=len(i)
            for j in range(1,4):##生成大小从1到3的候选项，暂时保存到item_count
                self.increase_ck_item(i,[],l,j,0,item_count)
        for item in item_count:#判断各候选项是否满足最小支持度min_support
            if item_count[item] >= min_support:
                L[len(item)-1].add(item)#满足条件，添加到指定的频繁项集中
                support_data[item] = item_count[item]
        return L

    def increase_ck_item(self,item,temp,l,size,index,item_count):#递归生成候选项(dfs方法)
        if len(temp)==size:
            ck_item=frozenset(temp)
            if ck_item not in item_count:
                item_count[ck_item]=1
            else:
                item_count[ck_item]+=1
            return
        for i in range(index,l):
            temp.append(item[i])
            self.increase_ck_item(item,temp,l,size,i+1,item_count)
            temp.pop()

    def create_ck(self,Lk_1,size):#通过频繁项集Lk-1创建ck候选项集
        Ck = set()
        l = len(Lk_1)
        lk_list = list(Lk_1)
        for i in range(l):
            for j in range(i+1, l):#两次遍历Lk-1，找出前n-1个元素相同的项
                l1 = list(lk_list[i])
                l2 = list(lk_list[j])
                l1.sort()
                l2.sort()
                if l1[0:size-2] == l2[0:size-2]:#只有最后一项不同时，生成下一候选项
                    Ck_item = lk_list[i] | lk_list[j]
                    if self.has_infrequent_subset(Ck_item, Lk_1):#检查该候选项的子集是否都在Lk-1中
                        Ck.add(Ck_item)
        return Ck

    def has_infrequent_subset(self,Ck_item, Lk_1):#检查候选项Ck_item的子集是否都在Lk-1中
        for item in Ck_item: 
            sub_Ck = Ck_item - frozenset([item])
            if sub_Ck not in Lk_1:
                return False
        return True

    def generate_lk_by_ck(self,data_set,ck,min_support,support_data):#通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
        item_count={}#用于标记各候选项在数据集出现的次数
        Lk = set()
        for t in tqdm(data_set):#遍历数据集
            for item in ck:#检查候选集ck中的每一项是否出现在事务t中
                if item.issubset(t):
                    if item not in item_count:
                        item_count[item] = 1
                    else:
                        item_count[item] += 1
        t_num = float(len(data_set))
        for item in item_count:#将满足支持度的候选项添加到频繁项集中
            if item_count[item] >= min_support:
                Lk.add(item)
                support_data[item] = item_count[item]
        return Lk
        
    def generate_L(self,data_set, min_support):#用于生成所有频繁项集的主函数，k为最大频繁项的大小
        support_data = {} #用于保存各频繁项的支持度
        L=self.create_l1_l3(data_set,support_data,min_support)
        Lksub=L[-1].copy() #初始时Lk-1=L3
        i=4
        while(True):
            Ci = self.create_ck(Lksub, i)  #根据Lk-1生成Ck
            Li = self.generate_lk_by_ck(data_set, Ci, min_support, support_data) #根据Ck生成Lk
            if len(Li)==0:break
            Lksub = Li.copy()  #下次迭代时Lk-1=Lk
            L.append(Lksub)
            i+=1
        for i in range(len(L)):
            print("frequent item {}：{}".format(i+1,len(L[i])))
        return L, support_data

    def generate_R(self,dataset, min_support, min_conf):
        L,support_data=self.generate_L(dataset,min_support)#根据频繁项集和支持度生成关联规则
        rule_list = []#保存满足置信度的规则
        sub_set_list = []#该数组保存检查过的频繁项
        for i in range(0, len(L)):
            for freq_set in L[i]:#遍历Lk
                for sub_set in sub_set_list:#sub_set_list中保存的是L1到Lk-1
                    if sub_set.issubset(freq_set):#检查sub_set是否是freq_set的子集
                        #检查置信度是否满足要求，是则添加到规则
                        conf = support_data[freq_set] / support_data[freq_set - sub_set]
                        big_rule = (freq_set - sub_set, sub_set, conf)
                        if conf >= min_conf and big_rule not in rule_list:
                            rule_list.append(big_rule)
                sub_set_list.append(freq_set)
        rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
        return rule_list

if __name__=="__main__":
    ##config

    # filename="药方.xls"
    # min_support=600#最小支持度
    # min_conf=0.9#最小置信度
    # size=8#频繁项最大大小
    filename="groceries.csv"
    min_support=25#最小支持度
    min_conf=0.7#最小置信度
    size=5#频繁项最大大小

    current_path=os.getcwd()
    if not os.path.exists(current_path+"/log"):
        os.mkdir("log")
    path=current_path+"/dataset/"+filename
    save_path=current_path+"/log/"+filename.split(".")[0]+"_apriori_hash.txt"

    data=load_data(path)
    apriori_h=Apriori_hash()
    rule_list=apriori_h.generate_R(data,min_support=15,min_conf=0.7)
    save_rule(rule_list,save_path)

