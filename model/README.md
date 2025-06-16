---
frameworks:
- Pytorch
license: Apache License 2.0
tasks:
- translation

#model-type:
##如 gpt、phi、llama、chatglm、baichuan 等
#- gpt

#domain:
##如 nlp、cv、audio、multi-modal
#- nlp

#language:
##语言代码列表 https://help.aliyun.com/document_detail/215387.html?spm=a2c4g.11186623.0.0.9f8d7467kni6Aa
#- cn 

#metrics:
##如 CIDEr、Blue、ROUGE 等
#- CIDEr

#tags:
##各种自定义，包括 pretrained、fine-tuned、instruction-tuned、RL-tuned 等训练方法和其他
#- pretrained

#tools:
##如 vllm、fastchat、llamacpp、AdaSeq 等
#- vllm
---
# 多语言翻译(m2m100_1.2B)

支持100种语言的相互翻译。

M2M100 is a multilingual encoder-decoder (seq-to-seq) model trained for Many-to-Many multilingual translation. It was introduced in [this paper](https://arxiv.org/abs/2010.11125) and first released in [this repository](https://github.com/pytorch/fairseq/tree/master/examples/m2m_100) .

The model that can directly translate between the 9,900 directions of 100 languages. To translate into a target language, the target language id is forced as the first generated token. To force the target language id as the first generated token, pass the forced_bos_token_id parameter to the generate method.

## 使用

https://openi.pcl.ac.cn/cubeai-model-zoo/hf_facebook_m2m100_1.2B

## 模型来源

https://hf-mirror.com/facebook/m2m100_1.2B
