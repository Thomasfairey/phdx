"use client";

import { useState } from "react";
import { Button, Input, Textarea, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui";
import { useGenerateOutline } from "@/hooks/use-writing";
import { useWritingStore } from "@/stores/writing-store";
import { Sparkles, Plus, X } from "lucide-react";

export function OutlineGenerator() {
  const [thesisTitle, setThesisTitle] = useState("");
  const [questions, setQuestions] = useState<string[]>([""]);
  const [chapterCount, setChapterCount] = useState(5);

  const { isGeneratingOutline } = useWritingStore();
  const generateOutline = useGenerateOutline();

  const addQuestion = () => {
    setQuestions([...questions, ""]);
  };

  const removeQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const updateQuestion = (index: number, value: string) => {
    const updated = [...questions];
    updated[index] = value;
    setQuestions(updated);
  };

  const handleGenerate = () => {
    const validQuestions = questions.filter(q => q.trim());
    if (!thesisTitle.trim() || validQuestions.length === 0) return;

    generateOutline.mutate({
      thesis_title: thesisTitle,
      research_questions: validQuestions,
      chapter_count: chapterCount,
    });
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-module-writing" />
          Generate Thesis Outline
        </CardTitle>
        <CardDescription>
          Provide your thesis title and research questions to generate a structured outline
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Thesis Title */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">
            Thesis Title
          </label>
          <Input
            placeholder="Enter your thesis title..."
            value={thesisTitle}
            onChange={(e) => setThesisTitle(e.target.value)}
          />
        </div>

        {/* Research Questions */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-text-primary">
            Research Questions
          </label>
          {questions.map((question, index) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder={`Research question ${index + 1}...`}
                value={question}
                onChange={(e) => updateQuestion(index, e.target.value)}
              />
              {questions.length > 1 && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeQuestion(index)}
                  className="text-text-tertiary hover:text-error"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={addQuestion}
            className="text-accent-primary"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Question
          </Button>
        </div>

        {/* Chapter Count */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">
            Number of Chapters
          </label>
          <Input
            type="number"
            min={3}
            max={10}
            value={chapterCount}
            onChange={(e) => setChapterCount(parseInt(e.target.value) || 5)}
            className="w-24"
          />
        </div>
      </CardContent>

      <CardFooter>
        <Button
          onClick={handleGenerate}
          loading={isGeneratingOutline}
          disabled={!thesisTitle.trim() || questions.every(q => !q.trim())}
          className="w-full"
        >
          <Sparkles className="w-4 h-4 mr-2" />
          Generate Outline
        </Button>
      </CardFooter>
    </Card>
  );
}
