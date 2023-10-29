import unittest
from tsstk import core  # 假设你在core.py中定义了具体的功能实现

class TestCoreFunctions(unittest.TestCase):

    def get_tss_from_bam(bam_files, output_tsv):
       # 创建一个字典来保存TSS信息
       tss_dict = {}
       # 遍历所有提供的BAM文件
       for bam_file in bam_files:
           # 使用pysam库读取BAM文件
           with pysam.AlignmentFile(bam_file, "rb") as bam:
               #遍历BAM文件中的每一个read
               for read in bam:
                  # 获得flag值
                  flag = read.flag
                  # 判断是否为primary alignment
                  if flag >= 256:
                      continue
                
                # 获取染色体名称和位置
                chr_name = read.reference_name
                position = read.reference_start   0-based
                
                #  根据flag判断链
                strand = '+' if flag == 0 else '-' if flag == 16 else None
                
                if strand is None:
                    continue
                # 保存TSS信息
                if chr_name not in tss_dict:
                    tss_dict[chr_name] = {}
                
                if strand not in tss_dict[chr_name]:
                    tss_dict[chr_name][strand] = []
                
                tss_dict[chr_name][strand].append(position + 1)   转为1-based
                
     # 将TSS信息写入TSV文件
     with open(output_tsv, 'w') as out_file:
         out_file.write("chr\tpos\tstrand\n")   # 写入表头
         for chr_name in sorted(tss_dict.keys()):
             for strand in sorted(tss_dict[chr_name].keys()):
                 for position in sorted(tss_dict[chr_name][strand]):
                     out_file.write(f"{chr_name}\t{position}\t{strand}\n")
                    
#  示例使用
#bam_files = ["file1.bam", "file2.bam"]
#output_tsv = "output_tss.tsv"
#get_tss_from_bam(bam_files, output_tsv)


        # 在这里写测试用于从BAM文件获取TSS信息的函数的代码
        pass
    
    def test_get_tss_from_table(self):
        # 在这里写测试用于从TSS表获取TSS信息的函数的代码
        pass

if __name__ == '__main__':
    unittest.main()

