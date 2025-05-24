import os
def inp_file_gen(rxn,pH_list, V_list, gases, concentrations, adsorbates, activity, Reactant1, Reactant2, Reactant3, Product1, Product2, Product3, Ea, Eb, P, Temp, Time, Abstol, Reltol):
        #path=os.path.join(children_folder,'input_file.mkm')
        inp_file = open("input_file.mkm",'w')
        inp_file.write('&compounds\n\n')
        inp_file.write("#gas-phase compounds\n\n#Name; isSite; concentration\n\n")
        for compound,concentration in zip(gases,concentrations):
            inp_file.write("{:<15}; 0; {}\n".format(compound,concentration))

        inp_file.write("\n\n#adsorbates\n\n#Name; isSite; activity\n\n")   
        for compound,concentration in zip(adsorbates,activity):
            inp_file.write("{:<15}; 1; {}\n".format(compound,concentration))

        inp_file.write("\n#free sites on the surface \n\n")
        inp_file.write("#Name; isSite; activity\n\n")   
        inp_file.write("*; 1; {}\n\n".format(1.0))    

        inp_file.write('&reactions\n\n')
        pre_exp=6.21e12
        for j in range(len(rxn)):
            if Reactant3[j]!="":
                line = "AR; {:<15} + {:<15} + {:<5} => {:<15}{:<15};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],Reactant2[j],Reactant3[j],Product1[j],Product2[j],pre_exp, pre_exp, Ea[j],Eb[j] )   
            elif Product3[j]!="":
                line = "AR; {:<15} + {:<14}  => {:<10} + {:<15} + {:<7};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],Reactant2[j],Product1[j],Product2[j],Product3[j],pre_exp, pre_exp, Ea[j],Eb[j] )     
            elif  Reactant2[j]!="" and Product2[j]!="":
                line = "AR; {:<15} + {:<15} => {:<15} + {:<20};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],Reactant2[j],Product1[j],Product2[j],pre_exp, pre_exp, Ea[j],Eb[j] )
            elif  Reactant2[j]=="" and Product2[j]!="":
                line = "AR; {:<15} {:<17} => {:<15} + {:<20};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],"",Product1[j],Product2[j],pre_exp, pre_exp, Ea[j],Eb[j] )
            elif Reactant2[j]!="" and Product2[j]=="":
                line = "AR; {:<15} + {:<15} => {:<15}{:<23};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],Reactant2[j],Product1[j],"",pre_exp, pre_exp, Ea[j],Eb[j] )
            elif Reactant2[j]=="" and Product2[j]=="":
                line = "AR; {:<15} {:<17} => {:<15}{:<23};{:<10.2e} ;  {:<10.2e} ;  {:<10} ;  {:<10} \n".format(Reactant1[j],"",Product1[j],"",pre_exp, pre_exp, Ea[j],Eb[j] )
            
            inp_file.write(line)    
        # Write settings
        inp_file.write("\n\n&settings\nTYPE = SEQUENCERUN\nPRESSURE = {}".format(P))
        inp_file.write("\nPOTAXIS=1\nDEBUG=0\nNETWORK_RATES=1\nNETWORK_FLUX=1\nUSETIMESTAMP=0")

        # Write run parameters
        inp_file.write('\n\n&runs\n')
        inp_file.write("# Temp; Potential;Time;AbsTol;RelTol\n")

        # Use first voltage if list
        if isinstance(V_list, list):
            V = V_list[0]
        else:
            V = V_list

        line2 = "{:<5};{:<5};{:<5.2e};{:<5};{:<5}".format(Temp, V, Time, Abstol, Reltol)
        inp_file.write(line2)
        inp_file.close()  

