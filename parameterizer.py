"""
Parameterizer.py
The initialization script for the Parameterizer tool
Part 1 of the WRF-FIRE Enhancement Toolkit

Author: Anthony DiBiase, MEM
        Duke University, Nicholas School of the Environment

This script is the framework for an ESRI python "add-in" tool for ArcMap v. 10.2.  
It is intended to ease the parameterization process of WRF-FIRE by easily developing 
a namelist.wps.  The user defines domains, and simply pushes a few buttons to print out 
a final namelist, suitable for import to the WRF Preprocessing Suite/geogrid.

Usage: import the .esriaddin file generated using this script and the pythonaddins wizard
to ArcMap, load a basemap, and go to town developing rectangular polygons for domains.

Limitations: Each domain must be "nested" completely within each parent.
I specify a workflow in the readme file bundled with this script.  Follow it, and there should be no problems.
Additionally: this module requires a healthy amount of user input, mostly involved in selecting files via pop-up boxes.
This is annoying, I understand, and I apologize.  It's the only method I could implement that allows for a variable number of domains.
Also, there's a lot of variable redundancy-again because of the uncertain amount of domains with changing attributes, need to constantly re-check
Also: there's the use of global variables here.  I know, bad form.  But it's necessary, b/c in python 2.7 you can't alter var's from one module when 
imported into another module.  x = A.x; x+=1 creates an error.  In this situation, the global variables shouldn't pose a problem if the user isn't 
an idiot.

Copyright Anthony DiBiase 2013

"""

#import modules used in the script as well as the global variables

import arcpy as ap
import pythonaddins
import os
import numpy

ap.env.overwriteOutput = True
domain_number = 0 
global_i = [1]
global_j = [1]

class calculateNest(object):
    """Implementation for parameterizer_final_addin.calculateNest (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        #get the inputs (theoretically I'd like to loop though and find parent i,j automatically, but there's a variable # of domains and master regions)
        master_domain = pythonaddins.OpenDialog("Select your Master Domain", False, "", "","","")
        nest = pythonaddins.OpenDialog("Select your next Nested Domain", False, "", "","","")
        #calculate extents and get the lat/lon origin of the nested domain
        desc1 = ap.Describe(master_domain)
        desc2 = ap.Describe(nest)
        ext_master = desc1.extent
        ext_nested = desc2.extent
        if ext_master.contains(ext_nested) == True: #check if it actually fits
            nest_x = ext_nested.XMin
            nest_y = ext_nested.YMin
            x_y = "%s %s"%(nest_x, nest_y)
            #get cell value of MASTER at the point from nest 
            cell_val = float(ap.GetCellValue_management(master_domain, x_y, "")[0])
            #with cell value, find index on numpy array
            my_array = ap.RasterToNumPyArray(master_domain)
            index = numpy.where(my_array == cell_val)
            max_rows = int(ap.GetRasterProperties_management(master_domain, "ROWCOUNT", "")[0])
            print "rows complete"
            def index_to_namelist(sample_index, rows): #using the actual index instead of calculating it based on geographic distance 
                i = int(sample_index[1])+1
                y = int(sample_index[0])
                j = rows - y
                return i, j
            i_temp, j_temp = index_to_namelist(index, max_rows)
            global global_i, global_j
            global_i.append(i_temp)
            global_j.append(j_temp)            
            print "The current nest indexes are: \ni: %r \nj:%r\nKeep on going until all nests are added" %(global_i, global_j)
        else:
            pythonaddins.MessageBox("DOMAIN ERROR: Nested domain is not contained within the Master Domain","DOMAIN ERROR!", 5)
            print "Try again!" #message box should get this, but keeping things consistent

class createDomain(object):
    """Implementation for parameterizer_final_addin.createDomain (Tool)"""
    def __init__(self):
        self.enabled = True
        self.cursor = 3
        self.shape = "Rectangle" #to ensure onRectangle works as planned
    def onRectangle(self, rectangle_geometry):
        #save the parameters for the domain
        file_loc = pythonaddins.SaveDialog("Save your file","", "")
        file_loc = os.path.split(file_loc) 
        out_path = file_loc[0]
        out_name = file_loc[1]
        resolution = setRes.text
        #and actually captures the extent used (onRectangle saves rectangle_geometry as an extent object)
        extent = rectangle_geometry
        #create temporary raster, then get unique cell values
        raster = ap.CreateRandomRaster_management(out_path, out_name, "NORMAL", extent, resolution)
        return raster #these rasters should generally 

class domainNumber(object):
    """Implementation for parameterizer_final_addin.domainNumber (ComboBox)"""
    def __init__(self):
        self.items = ["1","2","3","4"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
        self.hinttext = "Integer number of final domains"
    def onEditChange(self, text): #so if the user actually edits the box
        global domain_number
        number_domains = int(text)
        domain_number = number_domains
    def onSelChange(self, selection): #and if the user selects something in the box
        global domain_number
        number_domains = int(selection)
        domain_number = number_domains
        
class outPath(object):
    """Implementation for parameterizer_final_addin.outPath (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        output_loc = pythonaddins.OpenDialog("Select the location of your output wrf-fire (wps) directory",False, "", "", "", "")
        self.output_location = output_loc


class printFinal(object):
    """Implementation for parameterizer_final_addin.printFinal (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        #iterate through number of domains
        #note: select the nest and parent domain iteratively, starting with the original 'master'
        global domain_number
        counter = 0
        num = domain_number
        num = int(num)
        num_files = num-1
        #establish local var's
        e_we = [] 
        e_sn = []
        dx = 0
        dy = 0 
        parent_id = [1]
        parent_grid_ratio = [1] #done
        while counter < num_files:
            parent = pythonaddins.OpenDialog("Select the parent nest", False, "", "", "", "")
            nest = pythonaddins.OpenDialog("Select the nest", False, "", "", "", "")
            #ok, select values for the FIRST set (vars only needing one value)
            if counter == 0: 
                #cell res for original master
                dx = int(ap.GetRasterProperties_management(parent,"CELLSIZEX","")[0])
                dy = dx
                #domain geographic properties for the master (projected to geographic coordinates)
                scratch_raster = ap.ProjectRaster_management(parent, "in_memory\\scratch_raster", "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", "NEAREST", "", "", "", "")
                obj = ap.Describe(scratch_raster)
                ext = obj.extent
                ref_lon = float((ext.XMax + ext.XMin)/2) #to find the mean point in the center of the raster in terms of lat/lon
                ref_lat = float((ext.YMax + ext.YMin)/2) 
                truelat1 = float(ext.YMin)
                truelat2 = float(ext.YMax)
                stand_lon = ref_lon
                ap.Delete_management(scratch_raster, "") #clean up the memory workspace
            else:
                pass #so moves on if counter > 0
            #now calculate parent_grid ratio (auto-start w/ 1 for master domain)
            res_parent = ap.GetRasterProperties_management(parent, "CELLSIZEX", "")[0]
            res_nest = ap.GetRasterProperties_management(nest, "CELLSIZEX","")[0]
            ratio = int(res_parent)/int(res_nest)
            parent_grid_ratio.append(ratio)
            temp_ratios = [float(i) for i in parent_grid_ratio]
            #parent_id (domain id of the parent, starting with 1)
            id = counter+1
            parent_id.append(id) 
            #calculate e_sn, e_we (num cells in x,y directions)
            #define function first
            def domain_adjust(numbers, ratios):
                for i, (x, y) in enumerate(zip(numbers, ratios)):
                    if i == 0:
                        numbers[i] = int(x)
                    else:
                        if x%y == 0.0:
                            numbers[i] = int(numbers[i]+1.0)
                        else:
                            numbers[i] = int((round(x/y)*y)+1.0)
                return numbers
            e_sn.append(float(ap.GetRasterProperties_management(parent, "ROWCOUNT", "")[0])) #so get the individual value (overwritten every iteration)
            e_we.append(float(ap.GetRasterProperties_management(parent,"COLUMNCOUNT", "")[0])) #same as above
            if counter == num_files-1: #to get the final cell count on the list, on the final repetition
                e_sn.append(float(ap.GetRasterProperties_management(nest, "ROWCOUNT","")[0]))
                e_we.append(float(ap.GetRasterProperties_management(nest, "COLUMNCOUNT","")[0]))
                #now everything's accounted for, we need to shift things up a bit
                e_sn = domain_adjust(e_sn, temp_ratios)
                e_we = domain_adjust(e_we, temp_ratios)
            #to end the loop
            counter+=1
        #######now, all values should be appended to the list, so you just need to write them out
        #first, convert them to strings ending in a comma, rather than list objects 
        parent_id = ",".join([str(x) for x in parent_id])
        parent_grid_ratio = ",".join([str(x) for x in parent_grid_ratio])
        global global_i, global_j #call the global variables.  Global b/c you're altering them to a string below, not just printing them out
        i_parent_start = global_i
        j_parent_start = global_j
        i_parent_start = ",".join([str(x) for x in i_parent_start])
        j_parent_start = ",".join([str(x) for x in j_parent_start])
        e_sn = ",".join([str(x) for x in e_sn])
        e_we = ",".join([str(x) for x in e_we])
        data_path = selectData.geog_data_path
        #and print everything out to finish
        print "Writing out namelist.wps in %s"%outPath.output_location
        namelist = "%s\\namelist.wps" %outPath.output_location
        output_namelist = open(namelist, 'w')
        output_namelist.write("&share\n")
        output_namelist.write("wrf_core = 'ARW',\n")
        output_namelist.write("max_dom = %r,\n" %domain_number) 
        output_namelist.write("io_form_geogrid = 2,\n") #requires netcdf files, but those are pretty default
        output_namelist.write("/\n\n")
        output_namelist.write("&geogrid\n")
        output_namelist.write("parent_id= %s,\n" %parent_id) 
        output_namelist.write("parent_grid_ratio = %s,\n" %parent_grid_ratio) 
        output_namelist.write("i_parent_start = %s,\n" %i_parent_start)
        output_namelist.write("j_parent_start = %s,\n" %j_parent_start)
        output_namelist.write("e_we = %s, \n" %e_we)
        output_namelist.write("e_sn = %s, \n" %e_sn)
        output_namelist.write("geog_data_res = '30s'\n") ########change to input var w/ easy combo box
        output_namelist.write("dx = %i,\n" %dx)
        output_namelist.write("dy= %i, \n" %dy)
        output_namelist.write("map_proj = 'lambert',\n")
        output_namelist.write("ref_lat = %.10f,\n" %ref_lat)
        output_namelist.write("ref_lon = %.10f,\n" %ref_lon) 
        output_namelist.write("truelat1 = %.10f,\n" %truelat1)
        output_namelist.write("truelat2 = %.10f,\n" %truelat2) 
        output_namelist.write("stand_lon = %.10f,\n" %stand_lon) 
        output_namelist.write("geog_data_path '%s'\n" %data_path) 
        output_namelist.write("/")
        output_namelist.close()
        print "Done!"

class reset(object):
    """Implementation for parameterizer_final_addin.reset (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        global global_i, global_j
        global_i = [1]
        global_j = [1]
        print "The namelist.wps has been reset"


class selectData(object):
    """Implementation for parameterizer_final_addin.selectData (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        data_path = pythonaddins.OpenDialog("Select the location of your static data directory", False, "", "", "", "")
        self.geog_data_path = data_path
        print "geog_data_path = %s" %data_path #just to error check

class setRes(object):
    """Implementation for parameterizer_final_addin.setRes (ComboBox)"""
    def __init__(self):
        self.items = ["3000", "1000", "200", "100"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
        self.hinttext = "Cell resolution (m^2)" 
    def onEditChange(self, text):
        #so pass the text changed to a setRes.text, which can be passed to other functions
        self.text = text
    def onSelChange(self, selection):
        self.text = selection
        
