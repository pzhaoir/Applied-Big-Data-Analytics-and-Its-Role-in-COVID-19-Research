import pandas as pd
import tool_kit as tk #tool_kit supplies the session connections to the CAS knowledge graph

# Get graph session
session = tk.get_graph_session(False)

# Get the component_one results
component_one_query = session.run("""
match (dr:SmallMol {isDrug:true})-[r:smallMol2Target]->(g:Gene)-[]-(b)
where
dr.id <> "reg/" //and (dr.id='reg/120685112' or dr.id='reg/76420729' or dr.id='reg/59052')
and 
(b.id in ['GO_0075509','GO_0046718','GO_0007596','GO_0006897','GO_0019048','GO_0039663','GO_0019079','GO_0019068','GO_0019076','GO_0031396','GO_0000209','GO_0016579','GO_0000398','GO_0040029','GO_0006338','GO_0006914','GO_0046847','GO_0007049','GO_0006974'] 
or b.medgenID = 'C0919747'
)
and  ((toFloat(r.actVal) <= 10 and r.actUOM =  "uM") OR (r.actUOM = "nM" and toFloat(r.actVal) <= 10000))
and
(
 (not g.gene  in ['env', 'gag-pol', 'np', 'na', 'ul80', 'na', 'gag-pol', 'np', 'rxra', 'prpf4', 'prpf4b', 'sf3b3', 'mtrex', 'snrnp200', 'hnrnpa1', 'lyn', 'esr1', 'cdk3', 'csnk2a1', 'pkn2', 'tlk1', 'mapk1', 'pak4', 'rps6ka1', 'gak', 'riok2', 'pim3', 'mapk7', 'pim1', 'mapk3', 'mark4', 'prkaca', 'plg', 'serpinc1', 'proc', 'cyp4f2', 'plaur', 'npc1', 'atg4b', 'ulk1', 'vcp', 'ulk3', 'ulk2', 'becn1'] 
 and (r.actType contains "IC50" or toLower(r.actType) contains "ki" or toLower(r.actType) contains  'potency'))
 or
 (g.gene  in ['ul80', 'rxra', 'prpf4', 'prpf4b', 'sf3b3', 'mtrex', 'snrnp200', 'hnrnpa1', 'lyn', 'esr1', 'cdk3', 'csnk2a1', 'pkn2', 'tlk1', 'mapk1', 'pak4', 'rps6ka1', 'gak', 'riok2', 'pim3', 'mapk7', 'pim1', 'mapk3', 'mark4', 'prkaca', 'plg', 'serpinc1', 'proc', 'cyp4f2', 'plaur', 'npc1', 'atg4b', 'ulk1', 'vcp', 'ulk3', 'ulk2', 'becn1'] 
 and (r.actType contains "EC50" ))
)

return 
dr.id as regNum, 
collect(distinct g.gene) as genes,
collect(distinct b.id) + collect(distinct b.medgenID) as paths
""")
component_one_data = component_one_query.data()

# Convert to data frame to allow easy itteration over results
c1_df = pd.DataFrame(component_one_data)
c1_df

# Collect all gene names present
c1_genes = set()
for i in c1_df.itertuples():
    genes = i[2]
    for gene in genes:
        c1_genes.add(gene)
c1_genes = list(c1_genes)

# Identify genes >2 fold increased not identified in human designated results.
qry = session.run(f"""
match (g:Gene)-[r:causesExpressionChange]-(v:Virus {{name:'SARS-CoV-2'}})
where not g.gene in {c1_genes}
and r.foldChange >= 2
return g.gene
""")
data = qry.data()

#collect new gene names
two_fold_genes = list()
for item in data:
    two_fold_genes.append(item['g.gene'])
len(two_fold_genes)

# Get the component_two gene/paths/reg
component_two_query = session.run(f"""
match (dr:SmallMol {{isDrug:true}})-[r:smallMol2Target]->(g:Gene)-[]-(b:BiologicalProcess)
where
dr.id <> "reg/"
and  
g.gene in {two_fold_genes} //this is the list of gene >= 2 fold higher expression not in component_one of the query
and 
b.id in ["GO_0006954","GO_0019221","GO_0007186","GO_0071222","GO_0032496","GO_0045944","GO_0008285","GO_0001525","GO_0000122","GO_0007204","GO_0043065","GO_0042981","GO_0045893","GO_0042127","GO_0007165","GO_0006915"]
and  
((toFloat(r.actVal) <= 10 and r.actUOM =  "uM") OR (r.actUOM = "nM" and toFloat(r.actVal) <= 10000))
and
(r.actType contains "IC50" or toLower(r.actType) contains "ki" or toLower(r.actType) contains  'potency')

return 
dr.id as regNum, 
collect(distinct g.gene) as genes,
collect(distinct b.id) as paths
""")
component_two_data = component_two_query.data()


######################################

# These functions from tool_kit were used to calculate gene and pathway rarity 
# from the list of genes and pathways associated with 
# the small molecules from the above components:

def get_pathway_rarity(paths, session = session()):
    # This block will calculate pathway rarity
    pathway_rarity_query = session.run(f"""
    match (b:BiologicalProcess) where b.id in {paths}
    with collect(b) as bs
    unwind bs as b
    with (toFloat(1)/log(size(apoc.coll.toSet([(b)<-[]-(:Gene)<-[r:smallMol2Target]-(s:SmallMol {{isDrug:true}}) where ((r.actType="IC50" or toLower(r.actType)="ki" or toLower(r.actType)= 'potency' or r.actType = 'EC50') and ((toFloat(r.actVal) <= 10 and r.actUOM =  "uM") OR (r.actUOM = "nM" and toFloat(r.actVal) <= 10000)))|s])))) as bpSig
    return bpSig
    """)
    pathway_rarity = pathway_rarity_query.data()
    pathway_rarity_list = list()
    for item in pathway_rarity:
        pathway_rarity_list.append(item['bpSig'])
    return pathway_rarity_list

def get_gene_rarity(genes, session = session()):
    # This block will calculate the gene rarity
    gene_rarity_query = session.run(f"""
    match (g:Gene) where g.gene in {genes}
    with collect(g) as gds
    unwind gds as gd
    with (toFloat(1)/log(size(apoc.coll.toSet([(gd)<-[r:smallMol2Target]-(s:SmallMol {{isDrug:true}}) 
    where ((r.actType contains "IC50" or toLower(r.actType) contains "ki" or toLower(r.actType) contains 'potency' or r.actType contains 'EC50') 
    and ((toFloat(r.actVal) <= 10 and r.actUOM =  "uM") OR (r.actUOM = "nM" and toFloat(r.actVal) <= 10000)))|s])))) 
    as geneSig
    return geneSig
    """)
    gene_rarity = gene_rarity_query.data()
    gene_rarity_list = list()
    for item in gene_rarity:
        gene_rarity_list.append(item['geneSig'])
    return gene_rarity_list
