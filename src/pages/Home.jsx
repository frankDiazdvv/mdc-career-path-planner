import React, { useState, useEffect, useRef } from "react";
import { invokeLLM } from "@/api/geminiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, TrendingUp, Download, ChevronDown, ChevronUp } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import SummaryCard from "../components/pathway/SummaryCard";
import PathwayStep from "../components/pathway/PathwayStep";

export default function Home() {
  const [conversation, setConversation] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your ElevatePath career advisor. Tell me a bit about your interests — for example, what subjects or careers you’re curious about!",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pathways, setPathways] = useState([]);
  const [expanded, setExpanded] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  useEffect(() => {
    scrollToBottom();
  }, [conversation, pathways]);

  const handleSendMessage = async (message) => {
    const newConv = [
      ...conversation,
      { role: "user", content: message, timestamp: new Date().toISOString() },
    ];
    setConversation(newConv);
    setIsProcessing(true);

    try {
      const response = await invokeLLM({ prompt: message });
      console.log("AI response:", response);

      let parsedData = null;

      if (response.career_paths && Array.isArray(response.career_paths)) {
        parsedData = response.career_paths;
      } else if (response.pathway_data) {
        parsedData = [response];
      } else if (response.output) {
        try {
          const parsed = JSON.parse(response.output);
          parsedData = parsed.career_paths || [parsed];
        } catch {
          parsedData = [response.output];
        }
      }

      if (parsedData && parsedData.length > 0) {
        setPathways(parsedData);
        setConversation([
          ...newConv,
          {
            role: "assistant",
            content:
              parsedData.length > 1
                ? "Here are several academic pathways you could explore!"
                : "Here’s a personalized academic pathway based on your interests!",
            timestamp: new Date().toISOString(),
          },
        ]);
      } else {
        setConversation([
          ...newConv,
          {
            role: "assistant",
            content:
              "I'm not sure yet — could you tell me a bit more about what you’re interested in?",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
      setConversation([
        ...newConv,
        {
          role: "assistant",
          content:
            "Sorry, something went wrong while processing your request. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // 🧾 Export a single pathway to PDF
  const exportJSONToPDF = (pathway) => {
    if (!pathway) return;

    const doc = new jsPDF();
    let y = 20;

    const addLine = (text, bold = false) => {
      doc.setFont("helvetica", bold ? "bold" : "normal");
      doc.text(text, 15, y);
      y += 8;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    };

    addLine("Your Academic Pathway", true);

    const data = pathway.pathway_data || pathway;

    if (data.mdc_phase) {
      addLine("", true);
      addLine(`MDC Phase: ${data.mdc_phase.degree_name}`, true);
      addLine(`Duration: ${data.mdc_phase.duration_semesters} semesters`);
      addLine(`Total Cost: $${data.mdc_phase.total_cost}`);
      addLine(`Credits: ${data.mdc_phase.total_credits}`);
      addLine("Courses:");
      data.mdc_phase.courses.forEach((c) =>
        addLine(`  • ${c.code} - ${c.name} (${c.credits} cr)`)
      );
    }

    if (data.fiu_phase) {
      addLine("", true);
      addLine(`FIU Phase: ${data.fiu_phase.degree_name}`, true);
      addLine(`Transfer Credits: ${data.fiu_phase.transfer_credits}`);
      addLine(`Duration: ${data.fiu_phase.duration_semesters} semesters`);
      addLine(`Total Cost: $${data.fiu_phase.total_cost}`);
      addLine(`Remaining Credits: ${data.fiu_phase.remaining_credits}`);
      addLine("Required Courses:");
      data.fiu_phase.required_courses.forEach((c) =>
        addLine(`  • ${c.code} - ${c.name} (${c.credits} cr)`)
      );
    }

    if (data.advanced_phase) {
      if (data.advanced_phase.masters) {
        const m = data.advanced_phase.masters;
        addLine("", true);
        addLine(`Masters: ${m.degree_name}`, true);
        addLine(`Duration: ${m.duration_years} years`);
        addLine(`Cost: $${m.total_cost}`);
        addLine(`Credits: ${m.total_credits}`);
      }
      if (data.advanced_phase.phd) {
        const p = data.advanced_phase.phd;
        addLine("", true);
        addLine(`PhD: ${p.degree_name}`, true);
        addLine(`Duration: ${p.duration_years} years`);
        addLine(`Funding: ${p.funding_available ? "Yes" : "No"}`);
      }
    }

    if (data.total_summary) {
      addLine("", true);
      addLine("TOTAL SUMMARY", true);
      addLine(`Years: ${data.total_summary.total_years}`);
      addLine(`Total Cost: $${data.total_summary.total_cost}`);
      addLine(`Career Outlook: ${data.total_summary.career_outlook}`);
    }

    doc.save(`${pathway.career_goal || "My_Pathway"}.pdf`);
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-purple-900 via-white to-blue-50">
      <div className="max-w-5xl mx-auto px-4 py-12 md:py-20">
        {/* --- HEADER --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <div className="flex flex-row justify-center w-full mb-10">
            <img
              src="./ElevatePath_logo_flat.png"
              alt="ElevatePath Logo"
              className="h-30"
            />
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-4 tracking-tight">
            Find Your Academic Journey
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Chat with our AI advisor to create your personalized educational
            pathway.
          </p>
        </motion.div>

        {/* --- CHAT --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <Card className="border-slate-200 shadow-2xl">
            <CardContent className="p-6">
              <div className="h-[500px] flex flex-col">
                <div className="flex-1 overflow-y-auto mb-4 space-y-2 pr-2">
                  {conversation.map((msg, i) => (
                    <ChatMessage key={i} message={msg} />
                  ))}
                  {isProcessing && (
                    <div className="flex gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-linear-to-br from-blue-900 to-blue-700 flex items-center justify-center flex-shrink-0">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{
                            duration: 1,
                            repeat: Infinity,
                            ease: "linear",
                          }}
                        >
                          <Sparkles className="w-5 h-5 text-amber-400" />
                        </motion.div>
                      </div>
                      <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                        <p className="text-slate-600">Thinking...</p>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                <div className="border-t border-slate-200 pt-4">
                  <ChatInput
                    onSend={handleSendMessage}
                    disabled={isProcessing}
                    placeholder="Tell me about your educational goals..."
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* --- MULTIPLE PATHWAYS --- */}
        {pathways.length > 0 && (
          <div className="mt-12 space-y-10">
            {pathways.map((path, i) => {
              const isOpen = expanded[i];
              const toggle = () =>
                setExpanded((prev) => ({ ...prev, [i]: !isOpen }));

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.1, duration: 0.7 }}
                  className="bg-white border border-slate-200 rounded-2xl shadow-xl p-6"
                >
                  <div
                    className="flex justify-between items-center cursor-pointer mb-4"
                    onClick={toggle}
                  >
                    <h2 className="text-2xl font-bold text-slate-800">
                      Option {i + 1}: {path.career_goal || "Career Path"}
                    </h2>
                    {isOpen ? (
                      <ChevronUp className="w-6 h-6 text-slate-500" />
                    ) : (
                      <ChevronDown className="w-6 h-6 text-slate-500" />
                    )}
                  </div>

                  {isOpen && (
                    <div className="space-y-8">
                      {path.pathway_data?.mdc_phase && (
                        <PathwayStep
                          phase={path.pathway_data.mdc_phase}
                          index={0}
                          totalPhases={3}
                        />
                      )}
                      {path.pathway_data?.fiu_phase && (
                        <PathwayStep
                          phase={path.pathway_data.fiu_phase}
                          index={1}
                          totalPhases={3}
                        />
                      )}
                      {path.pathway_data?.advanced_phase?.masters && (
                        <PathwayStep
                          phase={path.pathway_data.advanced_phase.masters}
                          index={2}
                          totalPhases={3}
                        />
                      )}
                      {path.pathway_data?.total_summary && (
                        <SummaryCard summary={path.pathway_data.total_summary} />
                      )}
                      <div className="flex justify-end">
                        <button
                          onClick={() => exportJSONToPDF(path)}
                          className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <Download className="w-5 h-5" />
                          Export PDF
                        </button>
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
