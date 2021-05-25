import glob
import ecl_tokenizer as et

datas = glob.glob(r"C:\GitHub\opm-tests\**\*.DATA", recursive=True)

for data_file in datas:
    try:
        c = et.EclCase(data_file, verbose=False)
        #print(c)
    except Exception as e:
        print("ERR : Issue parsing data deck :", str(e))
