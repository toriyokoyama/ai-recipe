# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import CsvItemExporter

class AiRecipePipeline(object):
    
    def open_spider(self,spider):
        self.recipe_attr_exporters = {}
    
    def close_spider(self,spider):
        for exporter in self.recipe_attr_exporters.values():
            exporter.finish_exporting()

    def process_item(self, item, spider):
        for k, v in item.items():
            with open('{}.csv'.format(k),'wb') as f:
                exporter = CsvItemExporter(f)
                exporter.start_exporting()
                exp_dict = {}
                # get all lists from inner dict
                for d in zip(*list(v.values())):
                    # for the number of columns to export
                    for i in range(len(d)):
                        exp_dict[i] = d[i]
                    exporter.export_item(exp_dict)
        return item
